from nanome.util import Logs, IntEnum, auto

try:
    from nanome.util import reset_auto
except:
    def reset_auto():
        pass

import sys

class __CommandEnum(IntEnum):
    if sys.version_info >= (3, 6): # Tmp hack
        # Override for auto()
        def _generate_next_value_(name, start, count, last_values):
            return IntEnum._generate_next_value_(name, 0, count, last_values)
    else:
        pass

# /!\ /!\ /!\
# Values names are really important here, as they are hashed, and need to match Nanome
class _Commands(__CommandEnum):
    # Tmp hack
    reset_auto() #Not an enum

    #Control
    connect = auto()
    run = auto()
    advanced_settings = auto()

    #UI
    menu_response = auto()
    menu_toggle = auto()
    button_press = auto()
    button_hover = auto()
    slider_release = auto()
    text_submit = auto()
    text_change = auto()
    slider_change = auto()
    image_press = auto()
    image_hold = auto()
    image_release = auto()
    menu_transform_response = auto()

    #Structure
    workspace_response = auto()
    complex_list_response = auto()
    complexes_response = auto()
    structures_deep_update_done = auto()
    position_structures_done = auto()
    complex_add = auto()
    complex_remove = auto()
    bonds_add_done = auto()
    dssp_add_done = auto()
    compute_hbonds_done = auto()

    #Stream
    stream_create_done = auto()
    stream_feed = auto()
    stream_feed_done = auto()
    stream_interrupt = auto()

    #File
    directory_response= auto()
    file_response= auto()
    file_save_done= auto()

    #Macro
    get_macros_response = auto()

    # Presenter
    presenter_info_response = auto()
    presenter_change = auto()
    controller_transforms_response = auto()

    #Other
    upload_cryo_em_done = auto()
    load_file_done = auto()

# /!\ /!\ /!\
# Values names are really important here, as they are hashed, and need to match Nanome
class _Messages(__CommandEnum):
    # Tmp hack
    reset_auto() #Not an enum
    
    #Control
    connect = auto()
    plugin_list_button_set = auto()

    #UI
    menu_update = auto()
    content_update = auto()
    node_update = auto()
    menu_transform_set = auto()
    menu_transform_request = auto()
    notification_send = auto()
    hook_ui_callback = auto()

    #Structure
    structures_deep_update = auto()
    structures_shallow_update = auto()
    structures_zoom = auto()
    structures_center = auto()
    workspace_update = auto()
    workspace_request = auto()
    add_to_workspace = auto()
    complexes_request = auto()
    complex_list_request = auto()
    bonds_add = auto()
    dssp_add = auto()
    compute_hbonds = auto()

    #Streams
    stream_create = auto()
    stream_feed = auto()
    stream_destroy = auto()

    #File
    directory_request = auto()
    file_request = auto()
    file_save = auto()

    #Macro
    save_macro = auto()
    delete_macro = auto()
    run_macro = auto()
    stop_macro = auto()
    get_macros = auto()

    # Presenter
    presenter_info_request = auto()
    controller_transforms_request = auto()

    #Other
    upload_cryo_em = auto()
    open_url = auto()
    load_file = auto()

class _Hashes():
    CommandHashes = [None] * len(_Commands)
    MessageHashes = [None] * len(_Messages)

a_char_value = ord('a')
z_char_value = ord('z')

def hash_command(str):
    result = 0
    hit = 0
    for i in range(6):
        idx = i * 3 % len(str)
        char_value = ord(str[idx].lower()) - a_char_value
        result <<= 5
        if char_value < 0 or char_value > z_char_value - a_char_value:
            continue
        result |= char_value + 1
        hit += 1
        if hit >= 6:
            break
    return result

def init_hashes():
    hashes = dict()
    i = -1
    for command in _Commands:
        i += 1
        hash = hash_command(command.name)
        if hash in hashes:
            Logs.error("Command hash collision detected:", command.name, "and", hashes[hash])
            continue
        hashes[hash] = command.name
        _Hashes.CommandHashes[i] = hash

    hashes.clear()
    i = -1

    for command in _Messages:
        i += 1
        hash = hash_command(command.name)
        if hash in hashes:
            Logs.error("Message hash collision detected:", command.name, "and", hashes[hash])
            continue
        hashes[hash] = command.name
        _Hashes.MessageHashes[i] = hash

init_hashes()