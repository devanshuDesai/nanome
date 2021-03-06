from nanome.util import Logs, DirectoryRequestOptions, IntEnum, config
from nanome.util.enums import StreamDirection
from nanome._internal import _PluginInstance
from nanome._internal._process import _Bonding, _Dssp
from nanome._internal._network import _ProcessNetwork
from nanome._internal._network._commands._callbacks import _Messages
from nanome.api.ui import Menu
from nanome.api.streams import Stream

import inspect
import sys
import os

class PluginInstance(_PluginInstance):

    """
    | Base class of any Plugin class.
    | Constructor should never be called by the user as it is instantiated by network, when a session connects.
    | Start, update, and all methods starting by "on" can be overridden by user, in order to get requests results
    """
    def __init__(self):
        #!important: do not delete and leave empty to prevent double init.
        pass

    def __pseudo_init__(self):
        self.__menu = Menu() #deprecated
        self.__set_first = False

    @property
    def menu(self):
        if not self.__set_first:
            self.__set_first = True
            Logs.warning("The default menu (self.menu) is now deprecated and will be removed in a future version. Please use the ui.Menu() constructor to create the menu.")
        return self.__menu

    @menu.setter
    def menu(self, value):
        self.__set_first = True
        self.__menu = value

    def __new__(cls):
        n = super(PluginInstance, cls).__new__(cls)
        n.__pseudo_init__()
        return n

    def start(self):
        """
        | Called when user "Activates" the plugin
        """
        pass

    def update(self):
        """
        | Called when when instance updates (multiple times per second)
        """
        pass

    def on_run(self):
        """
        | Called when user presses "Run"
        """
        Logs.warning('Callback on_run not defined. Ignoring')

    def on_stop(self):
        """
        | Called when user disconnects or plugin crashes
        """
        pass

    def on_advanced_settings(self):
        """
        | Called when user presses "Advanced Settings"
        """
        Logs.warning('Callback on_advanced_settings not defined. Ignoring')

    def on_complex_added(self):
        """
        | Called whenever a complex is added to the workspace.
        """
        pass

    def on_complex_removed(self):
        """
        | Called whenever a complex is removed from the workspace.
        """
        pass

    def on_presenter_change(self):
        """
        | Called when room's presenter changes.
        """
        pass

    def request_workspace(self, callback = None):
        """
        | Request the entire workspace, in deep mode
        """
        id = self._network._send(_Messages.workspace_request)
        self._save_callback(id, callback)

    def request_complex_list(self, callback = None):
        """
        | Request the list of all complexes in the workspace, in shallow mode
        """
        id = self._network._send(_Messages.complex_list_request)
        self._save_callback(id, callback)

    def request_complexes(self, id_list, callback = None):
        """
        | Requests a list of complexes by their indices
        | Complexes returned contains the full structure (atom/bond/residue/chain/molecule)

        :param id_list: List of indices
        :type id_list: list of :class:`int`
        """
        id = self._network._send(_Messages.complexes_request, id_list)
        self._save_callback(id, callback)

    def update_workspace(self, workspace):
        """
        | Replace the current workspace in the scene by the workspace in parameter

        :param workspace: New workspace
        :type workspace: :class:`~nanome.api.structure.workspace.Workspace`
        """
        self._network._send(_Messages.workspace_update, workspace)

    def send_notification(self, type, message):
        """
        | Send a notification to the user

        :param type: Type of notification to send.
        :type workspace: :class:`~nanome.util.enums.NotificationTypes`
        :param message: Text to display to the user.
        :type message: str
        """
        #avoids unnecessary dependencies.
        #needs to match the command serializer.
        args = (type, message)
        self._network._send(_Messages.notification_send, args)

    def update_structures_deep(self, structures, callback = None):
        """
        | Update the specific molecular structures in the scene to match the structures in parameter.
        | Will also update descendent structures and can be used to remove descendent structures.

        :param structures: List of molecular structures to update.
        :type structures: list of :class:`~nanome.api.structure.base.Base`
        """
        id = self._network._send(_Messages.structures_deep_update, structures)
        self._save_callback(id, callback)

    def update_structures_shallow(self, structures):
        """
        | Update the specific molecular structures in the scene to match the structures in parameter
        | Only updates the structure's data, will not update children or other descendents.

        :param structures: List of molecular structures to update.
        :type structures: list of :class:`~nanome.api.structure.base.Base`
        """
        self._network._send(_Messages.structures_shallow_update, structures)

    def zoom_on_structures(self, structures, callback=None):
        """
        | Repositions and resizes the workspace such that the provided structure(s) will be in the 
        | center of the users view.

        :param structures: Molecular structure(s) to update.
        :type structures: list of :class:`~nanome.api.structure.base.Base`
        """
        id = self._network._send(_Messages.structures_zoom, structures)
        self._save_callback(id, callback)

    def center_on_structures(self, structures, callback=None):
        """
        | Repositions the workspace such that the provided structure(s) will be in the 
        | center of the world.

        :param structures: Molecular structure(s) to update.
        :type structures: list of :class:`~nanome.api.structure.base.Base`
        """
        id = self._network._send(_Messages.structures_center, structures)
        self._save_callback(id, callback)
        
    def add_to_workspace(self, complex_list):
        """
        | Add a list of complexes to the current workspace

        :param complex_list: List of Complexes to add
        :type complex_list: list of :class:`~nanome.api.structure.complex.Complex`
        """
        self._network._send(_Messages.add_to_workspace, complex_list)

    def update_menu(self, menu):
        """
        | Update the menu in Nanome

        :param menu: Menu to update
        :type menu: :class:`~nanome.api.ui.menu.Menu`
        """
        self._menus[menu.index] = menu
        self._network._send(_Messages.menu_update, menu)
        
    def update_content(self, content):
        """
        | Update a specific UI element (button, slider, list...)

        :param content: UI element to update
        :type content: :class:`~nanome.api.ui.ui_base`
        """
        self._network._send(_Messages.content_update, content)

    def update_node(self, node):
        """
        | Update a layout node and its children

        :param node: Layout node to update
        :type node: :class:`~nanome.api.ui.layout_node`
        """
        self._network._send(_Messages.node_update, node)

    def set_menu_transform(self, index, position, rotation, scale):
        """
        | Update the position, scale, and rotation of the menu

        :param index: Index of the menu you wish to update
        :type index: int
        :param position: New position of the menu
        :type position: :class:`~nanome.util.vector3`
        :param rotation: New rotation of the menu
        :type rotation: :class:`~nanome.util.quaternion`
        :param scale: New scale of the menu
        :type scale: :class:`~nanome.util.vector3`
        """
        self._network._send(_Messages.menu_transform_set,
                            (index, position, rotation, scale))

    def request_menu_transform(self, index, callback):
        """
        | Requests spacial information of the plugin menu (position, rotation, scale)

        :param index: Index of the menu you wish to read
        :type index: int
        """
        id = self._network._send(_Messages.menu_transform_request, index)
        self._save_callback(id, callback)

    def request_directory(self, path, callback = None, pattern = "*"):
        """
        | Requests the content of a directory on the machine running Nanome

        :param path: Path to request. E.g. "." means Nanome's running directory
        :type path: str
        :param pattern: Pattern to match. E.g. "*.txt" will match all .txt files. Default value is "*" (match everything)
        :type pattern: str
        """
        options = DirectoryRequestOptions()
        options._directory_name = path
        options._pattern = pattern
        id = self._network._send(_Messages.directory_request, options)
        self._save_callback(id, callback)

    def request_files(self, file_list, callback = None):
        """
        | Reads files on the machine running Nanome, and returns them

        :param file_list: List of file name (with path) to read. E.g. ["a.sdf", "../b.sdf"] will read a.sdf in running directory, b.sdf in parent directory, and return them
        :type file_list: list of :class:`str`
        """
        id = self._network._send(_Messages.file_request, file_list)
        self._save_callback(id, callback)

    def save_files(self, file_list, callback = None):
        """
        | Save files on the machine running Nanome, and returns result

        :param file_list: List of files to save with their content
        :type file_list: list of :class:`~nanome.util.file.FileSaveData`
        """
        id = self._network._send(_Messages.file_save, file_list)
        self._save_callback(id, callback)

    @Logs.deprecated("create_atom_stream")
    def create_stream(self, atom_indices_list, callback):
        id = self._network._send(_Messages.stream_create, (Stream.Type.position, atom_indices_list, StreamDirection.writing))
        self._save_callback(id, callback)

    @Logs.deprecated("create_writing_stream")
    def create_atom_stream(self, atom_indices_list, stream_type, callback):
        self.create_writing_stream(atom_indices_list, stream_type, callback)

    def create_writing_stream(self, atom_indices_list, stream_type, callback):
        """
        | Create a stream allowing to continuously update properties of many structures

        :param atom_indices_list: List of indices of all atoms that should be in the stream
        :type atom_indices_list: list of :class:`int`
        :param stream_type: Type of stream to create
        :type stream_type: list of :class:`~nanome.api.stream.Stream.Type`
        """
        id = self._network._send(_Messages.stream_create, (stream_type, atom_indices_list, StreamDirection.writing))
        self._save_callback(id, callback)

    def create_reading_stream(self, atom_indices_list, stream_type, callback):
        """
        | Create a stream allowing to continuously receive properties of many structures

        :param atom_indices_list: List of indices of all atoms that should be in the stream
        :type atom_indices_list: list of :class:`int`
        :param stream_type: Type of stream to create
        :type stream_type: list of :class:`~nanome.api.stream.Stream.Type`
        """
        id = self._network._send(_Messages.stream_create, (stream_type, atom_indices_list, StreamDirection.reading))
        self._save_callback(id, callback)

    def add_bonds(self, complex_list, callback, fast_mode=None):
        """
        | Calculate bonds
        | Needs openbabel to be installed

        :param complex_list: List of complexes to add bonds to
        :type complex_list: list of :class:`~nanome.api.structure.complex.Complex`
        """
        bonding = _Bonding(complex_list, callback, fast_mode)
        bonding._start()

    def add_dssp(self, complex_list, callback):
        """
        | Use DSSP to calculate secondary structures

        :param complex_list: List of complexes to add ribbons to
        :type complex_list: list of :class:`~nanome.api.structure.complex.Complex`
        """
        dssp = _Dssp(complex_list, callback)
        dssp._start()

    def upload_cryo_em(self, path, callback = None):
        """
        | Renders a Cryo EM map in nanome.

        :param path: path to the .map or .map.gz file containing the map.
        :type path: str
        """
        id = self._network._send(_Messages.upload_cryo_em, path)
        self._save_callback(id, callback)

    def open_url(self, url):
        """
        | Opens a URL in Nanome's computer browser

        :param url: url to open
        :type url: str
        """
        url = url.strip()
        if '://' not in url:
            url = 'http://' + url
        self._network._send(_Messages.open_url, url)

    def request_presenter_info(self, callback):
        """
        | Requests presenter account info (unique ID, name, email)
        """
        id = self._network._send(_Messages.presenter_info_request)
        self._save_callback(id, callback)

    def request_controller_transforms(self, callback):
        """
        | Requests presenter controller info (head position, head rotation, left controller position, left controller rotation, right controller position, right controller rotation)
        """
        id = self._network._send(_Messages.controller_transforms_request)
        self._save_callback(id, callback)

    class PluginListButtonType(IntEnum):
        run = 0
        advanced_settings = 1

    def set_plugin_list_button(self, button, text = None, usable = None):
        """
        | Set text and/or usable state of the buttons on the plugin connection menu in Nanome

        :param button: Button to set
        :type button: :class:`~ButtonType`
        :param text: Text displayed on the button. If None, doesn't set text
        :type text: str
        :param usable: Set button to be usable or not. If None, doesn't set usable text
        :type usable: bool
        """
        if button == PluginInstance.PluginListButtonType.run:
            current_text = [self._run_text]
            current_usable = [self._run_usable]
        else:
            current_text = [self._advanced_settings_text]
            current_usable = [self._advanced_settings_usable]
        
        if text == None:
            text = current_text[0]
        else:
            current_text[0] = text
        if usable == None:
            usable = current_usable[0]
        else:
            current_usable[0] = usable

        self._network._send(_Messages.plugin_list_button_set, (button, text, usable))

    def send_files_to_load(self, files_list, callback = None):
        files = []
        if not isinstance(files_list, list):
            files_list = [files_list]
        for file in files_list:
            full_path = file.replace('\\', '/')
            file_name = full_path.split('/')[-1]
            with open(full_path, 'rb') as content_file:
                data = content_file.read()
            files.append((file_name, data))

        id = self._network._send(_Messages.load_file, (files, True, True))
        self._save_callback(id, callback)

    @property
    def plugin_files_path(self):
        path = os.path.expanduser(config.fetch('plugin_files_path'))
        if not os.path.exists(path):
            os.makedirs(path)
        return path

    @property
    def custom_data(self):
        """
        Get custom data set with Plugin.set_custom_data

        :type: tuple of objects or None if no data has been set
        """
        return self._custom_data
        
class _DefaultPlugin(PluginInstance):
    def __init__(self):
        pass