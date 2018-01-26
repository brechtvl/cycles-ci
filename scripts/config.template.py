
# Devices
devices = [
    {'id': 'nvidia_titanxp',
     'name': 'NVidia Titan Xp',
     'os': 'Ubuntu Linux',
     'type': 'CUDA',
     'tile_size': 256,
     'sample_factor': 1.0,
     'runs': 3,
     'available': True},
    {'id': 'intel_4790k',
     'name': 'Intel i7-4790K',
     'os': 'Ubuntu Linux',
     'type': 'NONE',
     'tile_size': 32,
     'sample_factor': 1.0,
     'runs': 3,
     'available': False},
]

# System configuration commands before running server.
system_config_commands = [
    # Disable turboboost
    "echo \"1\" | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo",
    # Disable ASLR
    "echo \"0\" | sudo tee /proc/sys/kernel/randomize_va_space"
]

