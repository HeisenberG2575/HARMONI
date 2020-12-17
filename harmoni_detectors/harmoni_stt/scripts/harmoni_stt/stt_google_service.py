#!/usr/bin/env python3

# Common Imports
import rospy
import roslib

from harmoni_common_lib.constants import State
from harmoni_common_lib.service_server import HarmoniServiceServer
from harmoni_common_lib.service_manager import HarmoniServiceManager
import harmoni_common_lib.helper_functions as hf

# Specific Imports
from harmoni_common_lib.constants import State, DetectorNameSpace, SensorNameSpace, ActuatorNameSpace
from audio_common_msgs.msg import AudioData
from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types
from std_msgs.msg import String
import numpy as np
import os
import io


class STTGoogleService(HarmoniServiceManager):
    """
    Google service
    """

    def __init__(self, name, param):
        super().__init__(name)
        """ Initialization of variables and google parameters """
        self.sample_rate = param["sample_rate"]
        self.language = param["language_id"]
        self.audio_channel = param["audio_channel"]
        self.credential_path = param["credential_path"]
        self.subscriber_id = param["subscriber_id"]
        self.service_id = hf.get_child_id(self.name)

        """ Setup the google request """
        self.setup_google()

        """Setup the google service as server """
        self.response_text = ""
        self.data = b""

        #self.state = State.INIT

        """Setup publishers and subscribers"""
        rospy.Subscriber(
            SensorNameSpace.microphone.value + self.subscriber_id,
            AudioData,
            self.callback,
        )
        rospy.Subscriber("/audio/audio", AudioData, None)
        self.text_pub = rospy.Publisher(
            DetectorNameSpace.stt.value + self.service_id, 
            String, 
            queue_size=10
        )
        rospy.Subscriber(
            ActuatorNameSpace.web.value + self.subscriber_id,
            String,
            self._web_callback,
        )
        """Setup the stt service as server """
        self.state = State.INIT
        return
    def _web_callback(self, data):
        rospy.loginfo("DATA FROM WEB: " + data + " +++++++++")
        if data == "STOP":
            self.finished_message = True

    def pause_back(self, data):
        rospy.loginfo(f"pausing for data: {len(data.data)}")
        self.pause()
        rospy.sleep(int(len(data.data) / 30000))  # TODO calibrate this guess
        self.state = State.START
        return

    def setup_google(self):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.credential_path
        self.client = speech.SpeechClient()
        self.config = types.RecognitionConfig(
            encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=self.sample_rate,
            language_code=self.language,
            max_alternatives=1,
        )
        self.streaming_config = types.StreamingRecognitionConfig(
            config=self.config, interim_results=True
        )
        return

    def callback(self, data):
        """ Callback function subscribing to the microphone topic"""
        data = np.fromstring(data.data, np.uint8)
        # self.data = self.data.join(data)
        # self.data = data.data
        rospy.loginfo(self.state)
        if self.state == State.START:
            self.transcribe_stream_request(data)
        else:
            rospy.loginfo("Not Transcribing data")

    def transcribe_stream_request(self, data):
        # TODO: streaming transcription https://github.com/googleapis/python-speech/blob/master/samples/microphone/transcribe_streaming_infinite.py
        stream = self.data
        rospy.loginfo("Transcribing Stream")
        requests = (
            speech.StreamingRecognizeRequest(audio_content=chunk) for chunk in stream
        )
        responses = self.client.streaming_recognize(
            config=self.streaming_config, requests=requests
        )
        rospy.loginfo(f"Responses: {responses}")
        for response in responses:
            rospy.loginfo(f"Response items: {response}")
            # Once the transcription has settled, the first result will contain the
            # is_final result. The other results will be for subsequent portions of
            # the audio.
            for result in response.results:
                print("Finished: {}".format(result.is_final))
                print("Stability: {}".format(result.stability))
                alternatives = result.alternatives
                # The alternatives are ordered from most likely to least.
                for alternative in alternatives:
                    print("Confidence: {}".format(alternative.confidence))
                    print("Transcript: {}".format(alternative.transcript))
        return

    def transcribe_file_request(self, data):
        rate = ""  # TODO: TBD
        audio = {"content": data}
        try:
            rospy.loginfo("Request to google")
            operation = self.client.long_running_recognize(
                config=self.config, audio=audio
            )
            rospy.loginfo("Waiting for the operation to complete.")
            self.state = State.PAUSE
            response = operation.result()
            for result in response.results:
                self.data = b""
                alternative = result.alternatives[0]
                text = alternative.transcript
                rospy.loginfo("The response is %s" % (text))
                print(self.response_text)
                if text:
                    self.response_text = self.response_text + " " + text
                else:
                    if self.response_text:
                        rospy.loginfo("Heard:" + self.response_text)
                        self.text_pub.publish(self.response_text[1:])
                        self.response_text = ""
            self.state = State.START
        except rospy.ServiceException:
            self.start = State.FAILED
            rospy.loginfo("Service call failed")
            self.response_received = True
            self.result_msg = ""
        return

    def request(self, input_data):
        self.data = self.data.join(input_data)
        rospy.loginfo("Start the %s request" % self.name)
        self.state = State.START
        self.transcribe_stream_request(self.data)
        return

    def wav_to_data(self, path):
        with io.open(path, "rb") as f:
            content = f.read()
        return content

    def start(self, rate=""):
        rospy.loginfo("Start the %s service" % self.name)
        if self.state == State.INIT:
            self.state = State.START
            # self.transcribe_stream()  # Start the microphone service at the INIT
        else:
            self.state = State.START
        return

    def stop(self):
        rospy.loginfo("Stop the %s service" % self.name)
        try:
            # self.close_stream()
            self.state = State.SUCCESS
        except Exception:
            self.state = State.FAILED
        return

    def pause(self):
        rospy.loginfo("Pause the %s service" % self.name)
        self.state = State.SUCCESS
        return


def main():
    service_name = DetectorNameSpace.stt.name
    name = rospy.get_param("/name_" + service_name + "/")
    test = rospy.get_param("/test_" + service_name + "/")
    test_input = rospy.get_param("/test_input_" + service_name + "/")
    test_id = rospy.get_param("/test_id_" + service_name + "/")
    try:
        rospy.init_node(service_name)
        param = rospy.get_param(name + "/" + test_id + "_param/")
        if not hf.check_if_id_exist(service_name, test_id):
            rospy.logerr(
                "ERROR: Remember to add your configuration ID also in the harmoni_core config file"
            )
            return
        service = hf.set_service_server(service_name, test_id)
        s = STTGoogleService(service, param)
        service_server = HarmoniServiceServer(name=service, service_manager=s)
        if test:
            rospy.loginfo("Testing the %s" % (service))
            data = s.wav_to_data(test_input)
            s.transcribe_file_request(data)
        else:
            service_server.update_feedback()
            rospy.spin()
    except rospy.ROSInterruptException:
        pass


if __name__ == "__main__":
    main()
