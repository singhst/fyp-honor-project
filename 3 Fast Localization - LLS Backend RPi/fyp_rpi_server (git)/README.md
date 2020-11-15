Last update:
2020.02.29

Structure:
fyp_rpi_server
├── mymodule
│   ├── kalman
│   │   ├── kalman.py
│   │   └── README.md
│   ├── submodule
│   │   ├── __init__.py
│   │   └── CoordinateSystem_v2.py
│   ├── __init__.py
│   ├── myHttpInterface.py
│   ├── myLLS_v2.py
│   ├── myNCR_v2.py
│   ├── myRssiFilter_v1.py
│   └── RadioPropagation_v2.py
├── flask_lls.py
├── performLocalization.py
└── README.md

=====================================
The main python script is: flask_lls.py
Just need to run the `flask_lls.py` to start the Flask Web Application.
