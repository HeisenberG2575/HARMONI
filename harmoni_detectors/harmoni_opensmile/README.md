# HARMONI Custom Detector



## Setup

## Usage

Run the following commands in order to run camera service and custom service :

```  bash
roslaunch harmoni_opensmile opensmile_service.launch
```

While in the harmoni_full_detector container, you can run opneface service:

```  bash
roslaunch harmoni_openface openface_service.launch
```

It returns a boolean with interaction rupture dection (1: present, 0: absent )

## Testing

