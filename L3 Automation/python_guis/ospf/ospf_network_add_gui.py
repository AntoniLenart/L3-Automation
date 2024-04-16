import tkinter as tk
from tkinter import messagebox

from resources.devices.Router import Router
from python_guis.gui_resources import config
from resources.routing_protocols.Network import Network
from resources.routing_protocols.ospf.OSPFArea import OSPFArea
import ipaddress


class OSPFNetworkAddGUI:
    def __init__(self, router: Router, ospf_area: OSPFArea, ospf_config_gui):
        self.hostname = router.name
        self.area = ospf_area
        self.ospf_config_gui = ospf_config_gui

        root = tk.Toplevel()
        # ######## WINDOW PARAMETERS ######## #
        # title
        root.title(config.APPNAME + ' ' + config.VERSION + ' ' + self.hostname + ' Area ' + ospf_area.id +
                   ' Add Network')

        # window icon, using conversion to iso, cause tkinter doesn't accept jpg
        icon = tk.PhotoImage(file=config.WINDOW_ICON_PATH)
        root.wm_iconphoto(False, icon)

        # size parameters
        width = 400
        height = 300
        screenwidth = root.winfo_screenwidth()
        screenheight = root.winfo_screenheight()
        alignstr = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
        root.geometry(alignstr)
        root.resizable(width=True, height=True)

        root.minsize(300, 300)

        lblNetwork = tk.Label(root, text='Network:')

        NetworkFrame = tk.Frame(root)
        entryIPNetworkFirst = tk.Entry(NetworkFrame, width=10)
        entryIPNetworkFirst.pack(side='left')
        labelDot1 = tk.Label(NetworkFrame, text='.')
        labelDot1.pack(side='left')

        entryIPNetworkSecond = tk.Entry(NetworkFrame, width=10)
        entryIPNetworkSecond.pack(side='left')
        labelDot2 = tk.Label(NetworkFrame, text='.')
        labelDot2.pack(side='left')

        entryIPNetworkThird = tk.Entry(NetworkFrame, width=10)
        entryIPNetworkThird.pack(side='left')
        labelDot3 = tk.Label(NetworkFrame, text='.')
        labelDot3.pack(side='left')

        entryIPNetworkFourth = tk.Entry(NetworkFrame, width=10)
        entryIPNetworkFourth.pack(side='left')

        lblMask = tk.Label(root, text='Mask:')
        entryMask = tk.Entry(root, width=5)

        lblNetwork.pack()
        NetworkFrame.pack()
        lblMask.pack()
        entryMask.pack()

        def get_network() -> str:
            ip = (entryIPNetworkFirst.get() + '.' + entryIPNetworkSecond.get() + '.' + entryIPNetworkThird.get() + '.' +
                  entryIPNetworkFourth.get())
            try:
                ipaddress.ip_address(ip)
                return ip
            except ValueError:
                messagebox.showerror('Error', 'Incorrect IP Format', parent=root)
                clean_entries()

        def get_mask() -> int:
            return int(entryMask.get())

        def clean_entries() -> None:
            ip_entries = [entryIPNetworkFirst, entryIPNetworkSecond, entryIPNetworkThird,
                          entryIPNetworkFourth]
            for entry in ip_entries:
                entry.delete(0, 'end')
            entryMask.delete(0, 'end')

        def validate_network() -> bool:
            ip_entries = [entryIPNetworkFirst, entryIPNetworkSecond, entryIPNetworkThird, entryIPNetworkFourth]
            network = ''
            for entry in ip_entries:
                value = entry.get()
                network += value + '.'
            network = network.rstrip('.')
            mask = entryMask.get()
            try:
                ipaddress.ip_network(network + '/' + mask)
                return True
            except ValueError:
                messagebox.showerror('Error', 'Incorrect Network', parent=root)
                clean_entries()
                return False

        def apply_network():
            if validate_network():
                network = get_network()
                mask = get_mask()
                from resources import constants
                wildcard = constants.WILDCARD_MASK[str(mask)]
                messagebox.showinfo('Network added', 'Network added', parent=root)

                network = Network(network=network,
                                  mask=mask,
                                  wildcard=wildcard)
                router.ospf.areas[self.area.id].networks[network.network] = network

                self.ospf_config_gui.insert_network(network)
                clean_entries()

        btnApply = tk.Button(root, text='Apply', command=apply_network)
        btnApply.pack(pady=5)
        btnQuit = tk.Button(root, text='Quit', command=root.destroy)
        btnQuit.pack()

        root.mainloop()
