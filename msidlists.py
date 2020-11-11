#!/usr/bin/env python

voltage_msids = ['2P24VAVL',  # 24 V bus EED voltage,
                 '2P15VAVL',  # +15 V bus EED voltage
                 '2P05VAVL',  # +05 V bus EED voltage
                 '2N15VAVL'  # +15 V bus EED voltage
                 ]

voltage_msids_b = ['2P24VBVL',  # 24 V bus EED voltage,
                   '2P15VBVL',  # +15 V bus EED voltage
                   '2P05VBVL',  # +05 V bus EED voltage
                   '2N15VBVL'  # +15 V bus EED voltage
                   ]

temperature_msids = [
    "2FE00ATM",  # Front-end Temperature (c)
    "2LVPLATM",  # LVPS Plate Temperature (c)
    "2IMHVATM",  # Imaging Det HVPS Temperature (c)
    "2IMINATM",  # Imaging Det Temperature (c)
    "2SPHVATM",  # Spectroscopy Det HVPS Temperature (c)
    "2SPINATM",  # Spectroscopy Det Temperature (c)
    "2PMT1T",  # PMT 1 EED Temperature (c)
    "2PMT2T",  # PMT 2 EED Temperature (c)
    "2DCENTRT",  # Outdet2 EED Temperature (c)
    "2FHTRMZT",  # FEABox EED Temperature (c)
    "2CHTRPZT",  # CEABox EED Temperature (c)
    "2FRADPYT",  # +Y EED Temperature (c)
    "2CEAHVPT",  # -Y EED Temperature (c)
    "2CONDMXT",  # Conduit Temperature (c)
    "2UVLSPXT",  # Snout Temperature (c)
    # CEA Temperature 1 (c) THESE HAVE FEWER POINTS AS THEY WERE RECENTLY ADDED BY TOM
    "2CE00ATM",
    # CEA Temperature 2 (c) THESE HAVE FEWER POINTS AS THEY WERE RECENTLY ADDED BY TOM
    "2CE01ATM",
    "2FEPRATM",  # FEA PreAmp (c)
    # Selected Motor Temperature (c) THIS IS ALWAYS 5 DEGREES THROUGHOUT ENTIRE MISSION
    "2SMTRATM",
    "2DTSTATT"   # OutDet1 Temperature (c)
]


monitor_temperature_msids = [
    "2FE00ATM",  # Front-end Temperature (c)
    "2LVPLATM",  # LVPS Plate Temperature (c)
    "2IMHVATM",  # Imaging Det HVPS Temperature (c)
    "2IMINATM",  # Imaging Det Temperature (c)
    "2SPHVATM",  # Spectroscopy Det HVPS Temperature (c)
    "2SPINATM",  # Spectroscopy Det Temperature (c)
    "2PMT1T",  # PMT 1 EED Temperature (c)
    "2PMT2T",  # PMT 2 EED Temperature (c)
    "2DCENTRT",  # Outdet2 EED Temperature (c)
    "2FHTRMZT",  # FEABox EED Temperature (c)
    "2CHTRPZT",  # CEABox EED Temperature (c)
    "2FRADPYT",  # +Y EED Temperature (c)
    "2CEAHVPT",  # -Y EED Temperature (c)
    "2CONDMXT",  # Conduit Temperature (c)
    "2UVLSPXT",  # Snout Temperature (c)
    # # CEA Temperature 1 (c) THESE HAVE FEWER POINTS AS THEY WERE RECENTLY ADDED BY TOM
    # "2CE00ATM",
    # # CEA Temperature 2 (c) THESE HAVE FEWER POINTS AS THEY WERE RECENTLY ADDED BY TOM
    # "2CE01ATM",
    "2FEPRATM",  # FEA PreAmp (c)
    # # Selected Motor Temperature (c) THIS IS ALWAYS 5 DEGREES THROUGHOUT ENTIRE MISSION
    # "2SMTRATM",
    "2DTSTATT"   # OutDet1 Temperature (c)
]


critical_anomaly_temps = [
    # "2FE00ATM",  # Front-end Temperature (c)
    # "2LVPLATM",  # LVPS Plate Temperature (c)
    "2IMHVATM",  # Imaging Det HVPS Temperature (c)
    "2IMINATM",  # Imaging Det Temperature (c)
    "2SPHVATM",  # Spectroscopy Det HVPS Temperature (c)
    "2SPINATM",  # Spectroscopy Det Temperature (c)
    # "2PMT1T",  # PMT 1 EED Temperature (c)
    # "2PMT2T",  # PMT 2 EED Temperature (c)
    # "2DCENTRT",  # Outdet2 EED Temperature (c)
    "2FHTRMZT",  # FEABox EED Temperature (c)
    "2CHTRPZT",  # CEABox EED Temperature (c)
    "2FRADPYT",  # +Y EED Temperature (c)
    "2CEAHVPT",  # -Y EED Temperature (c)
    "2CONDMXT",  # Conduit Temperature (c)
    "2UVLSPXT",  # Snout Temperature (c)
    # CEA Temperature 1 (c) THESE HAVE FEWER POINTS AS THEY WERE RECENTLY ADDED BY TOM
    "2CE00ATM",
    # CEA Temperature 2 (c) THESE HAVE FEWER POINTS AS THEY WERE RECENTLY ADDED BY TOM
    "2CE01ATM",
    "2FEPRATM",  # FEA PreAmp (c)
    # Selected Motor Temperature (c) THIS IS ALWAYS 5 DEGREES THROUGHOUT ENTIRE MISSION
    "2SMTRATM",
    "2DTSTATT"   # OutDet1 Temperature (c)
]

motor_msids = ["2DRLSOP",  # Door Primary Limit Switch Open (0 = not open)
               "2DRLSCL",  # Door Primary Limit Switch Closed (0 = not open)
               "2PYLSHM",  # +Y Shutter Primary LS Home (0 = not home)
               "2PYLSMX",  # +Y Shut LS Max ([un]act)
               "2MYLSHM",  # -Y Shut LS Home ([un]act)
               "2MYLSMX",  # -Y SHUTTER PRIMARY LIM SWITCH MAX TRAVEL
               "2CSLSHM",  # Cal Source Primary Limit Switch Home
               "2CSLSMX",  # Cal Source primary limit switch max travel
               "2FSPYST",  # Failsafe +Y shutter on/off (0 = ena)
               "2FSNYST",  # Failsafe -Y shutter on/off (0 = ena)
               "2NYMTAST",  # -Y SHUTTER MOTOR SELECTED
               "2PYMTAST",  # +Y SHUTTER MOTOR SELECTED
               "2CLMTAST",  # CALSRC MOTOR SELECTED
               "2DRMTAST",  # DOOR MOTOR SELECTED
               "2ALMTAST",  # ALL MOTORS DESELECTED
               "2MSMDARS",  # MOTION CONTROL MODE RESET
               "2MDIRAST",  # MOTOR DIRECTION (TRWD A,B)
               "2MSNBAMD",  # MTR STAT REG MV NSTEPS TRWD "B"
               "2MSNAAMD",  # MTR STAT REG MV NSTEPS TWRD "A"
               "2MSLBAMD",  # MTR STAT REG MV TO LS "B"
               "2MSLAAMD",  # MTR STAT REG MV TO LS "A"
               "2MSPRAMD",  # MTR STAT REG MV TO POS REG
               "2MSDRAMD",  # MTR DRIVE ENABLE
               "2MCMDARS",  # MOTION CONTROL MODE RESET
               "2MCNBAMD",  # MTR CMD REG MV NSTEPS TRWD "B"
               "2MCNAAMD",  # MTR CMD REG MV NSTEPS TWRD "A"
               "2MCLBAMD",  # MTR CMD REG MV TO LS "B"
               "2MCLAAMD",  # MTR CMD REG MV TO LS "A"
               "2MCPRAMD",  # MTR CMD REG MV TO POS REG
               "2MDRVAST",  # MTR DRIVE ENABLE
               "2SCTHAST",  # STEP CTR LAST VAL (HI BYTE)
               "2SCTHAST",  # STEP CTR LAST VAL (LO BYTE)
               "2SMOIAST",  # SELECTED MOTOR OVERCURRENT FLAG
               "2SMOTAST",  # SELECTED MOTOR OVERTEMP FLAG
               "2DROTAST",  # DRV OVERTEMP ENABLE
               "2DROIAST"  # DRV OVERCURRENT ENABLE
               ]


davec_temperature_msids = [
    "2PMT1T",  # PMT 1 EED Temperature (c)
    "2PMT2T",  # PMT 2 EED Temperature (c)
    "2DTSTATT",   # OutDet1 Temperature (c)
    "2DCENTRT",  # OutDet2
    "2FHTRMZT",  # FEABox EED Temperature (c)
    "2CHTRPZT",  # CEABox EED Temperature (c)
    "2FRADPYT",  # +Y EED Temperature (c)
    "2CEAHVPT",  # -Y EED Temperature (c)
    "2CONDMXT",  # Conduit Temperature (c)
    "2UVLSPXT",  # Snout Temperature (c)
    "2CE00ATM",
    "2CE01ATM"
]


rate_msids = ['2TLEV1RT',  # The Total Event Rate
              '2VLEV1RT',  # VAlie Event Rate
              '2SHEV1RT',  # Shield Event Rate
              ]


all_relevant_hrc_msids = ["2SHEV1RT",  # HRC AntiCo Shield Rates (1)
                          "2TLEV1RT",  # HRC Detector Event Rates (c/s) (1)
                          "2PRBSVL",   # Primary Bus Voltage (V)
                          "2PRBSCR",   # Primary Bus Current (amps)
                          "2C05PALV",  # +5V Bus Monitor
                          "2C15NALV",  # -15V Bus Monitor
                          "2C15PALV",  # +15V Bus Monitor
                          "2C24PALV",  # +24V Bus Monitor
                          "2FE00ATM",  # Front-end Temperature (c)
                          "2LVPLATM",  # LVPS Plate Temperature (c)
                          "2IMHVATM",  # Imaging Det HVPS Temperature (c)
                          "2IMINATM",  # Imaging Det Temperature (c)
                          # Spectroscopy Det HVPS Temperature (c)
                          "2SPHVATM",
                          "2SPINATM",  # Spectroscopy Det Temperature (c)
                          "2PMT1T",    # PMT 1 EED Temperature (c)
                          "2PMT2T",    # PMT 2 EED Temperature (c)
                          "2DCENTRT",  # Outdet2 EED Temperature (c)
                          "2FHTRMZT",  # FEABox EED Temperature (c)
                          "2CHTRPZT",  # CEABox EED Temperature (c)
                          "2FRADPYT",  # +Y EED Temperature (c)
                          "2CEAHVPT",  # -Y EED Temperature (c)
                          "2CONDMXT",  # Conduit Temperature (c)
                          "2UVLSPXT",  # Snout Temperature (c)
                          "2CE00ATM",  # CEA Temperature 1 (c)
                          "2CE01ATM",  # CEA Temperature 2 (c)
                          "2FEPRATM",  # FEA PreAmp (c)
                          "2SMTRATM",  # Selected Motor Temperature (c)
                          "2DTSTATT"  # OutDet1 Temperature (c)
                          ]

spacecraft_orbit_pseudomsids = ["Dist_SatEarth",  # Chandra-Earth distance (from Earth Center) (m)
                                # Pointing-Solar angle (from center) (deg)
                                "Point_SunCentAng"
                                ]


# Times flagged as Secondary Science Corruption
secondary_science_corruption = ["HRC_SS_HK_BAD"]

mission_events = ["obsids",
                  "orbits",
                  "dsn_comms",
                  "dwells",
                  "eclipses",
                  "rad_zones",
                  "safe_suns",
                  "scs107s",
                  "major_events"]


dashboard_msids = [["2P24VBVL", "2P15VBVL", "2N15VBVL", "2P05VBVL", "2C05PALV", "2C15PALV", "2C15NALV", "2C24PALV"],
                   ["2PRBSVL"],
                   ["2PRBSCR"],
                   ["2PMT1T", "2PMT2T"],
                   ["2DTSTATT", "2DCENTRT"],
                   ["2FHTRMZT", "2FRADPYT", "2FEPRATM", "2FE00ATM"],
                   ["2CHTRPZT", "2CEAHVPT"],
                   ["2SPINATM", "2IMINATM"],
                   ["2LVPLATM"],
                   ["2SPHVATM", "2IMHVATM"],
                   ["2TLEV1RT", "2VLEV1RT", "2SHEV1RT"],
                   ["AOSARES1"]]

dashboard_tiles = ["Bus Voltages",
                   "S/C Bus Voltage",
                   "S/C Bus Current",
                   "PMT Temperatures",
                   "Detector Housing Temp",
                   "FEA Temps",
                   "CEA Temps",
                   "Spec & Im Det Temps",
                   "LVPS Plate Temp",
                   "Spec & Im HVPS Temps",
                   "Shield & Event Rates",
                   "Spacecraft Pitch (Solar Array Angle)"]

dashboard_units = ["Voltage (V)",
                   "Voltage (V)",
                   "Current (A)",
                   "Temperature (C)",
                   "Temperature (C)",
                   "Temperature (C)",
                   "Temperature (C)",
                   "Temperature (C)",
                   "Temperature (C)",
                   "Temperature (C)",
                   r"Counts s$^{-1}$",
                   "Degrees"]

dashboard_limits = [(-20, 30),
                    (26, 32),
                    (1.4, 2.7),
                    (10, 35),
                    (10, 35),
                    (10, 35),
                    (10, 35),
                    (10, 35),
                    (20, 35),
                    (30, 40),
                    (10, 7000),
                    (40, 190)
                    ]
