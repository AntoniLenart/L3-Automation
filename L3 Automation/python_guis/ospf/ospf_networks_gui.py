import threading
import tkinter as tk
import tkinter.ttk
from python_guis.gui_resources import config
from python_guis.ospf.ospf_network_add_gui import OSPFNetworkAddGUI
from resources.connect_frontend_with_backend.frontend_backend_functions import remove_ospf_area_networks
from resources.devices.Router import Router
from resources.routing_protocols.Network import Network
from resources.user.User import User


class OSPFNetworksGUI:
    def __init__(self, main_gui, router: Router, user: User, area_id):
        area = str(area_id)
        root = tk.Toplevel()

        # title
        root.title(config.APPNAME + ' ' + config.VERSION + ' ' + router.name + ' Area ' + area +
                   ' OSPF Networks Configuration')
        # window icon, using conversion to iso, cause tkinter doesn't accept jpg
        icon = tk.PhotoImage(file=config.WINDOW_ICON_PATH)
        root.wm_iconphoto(False, icon)

        # size parameters
        width = 400
        height = 400
        screenwidth = root.winfo_screenwidth()
        screenheight = root.winfo_screenheight()
        alignstr = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
        root.geometry(alignstr)
        root.resizable(width=True, height=True)

        root.minsize(400, 400)

        root.grid_columnconfigure(1, weight=1)
        root.grid_columnconfigure(1, weight=1)

        treeFrame = tk.Frame(root)
        scrollbar = tk.Scrollbar(treeFrame, orient='vertical')
        scrollbar.pack(side='right', fill='y')

        treeColumns = ('No', 'Network', 'Mask')
        self.tree = tk.ttk.Treeview(treeFrame, columns=treeColumns, show='headings')
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side='left', fill='both', expand=True)

        scrollbar.config(command=self.tree.yview)

        self.tree.heading(treeColumns[0], text='No', anchor='w')
        self.tree.column(treeColumns[0], width=15)

        self.tree.heading(treeColumns[1], text='Network', anchor='w')
        self.tree.column(treeColumns[1], width=50)

        self.tree.heading(treeColumns[2], text='Mask', anchor='w')
        self.tree.column(treeColumns[2], width=30)

        i = 1
        for k, network in router.ospf.areas[area].networks.items():
            values = (i, network.network, network.mask)
            self.tree.insert('', tk.END, iid=i-1, values=values)
            i += 1

        treeFrame.grid(column=0, row=3, columnspan=2, sticky='NEWS')

        def add_network(router, area, self):
            OSPFNetworkAddGUI(main_gui, router, user, router.ospf.areas[area], self)

        def remove_network() -> None:
            item = self.tree.selection()
            # todo 29
            network_and_wildcard = [network, wildcard]
            threading.Thread(target=remove_ospf_area_networks,
                             args=(main_gui, router, user, router.ospf.areas[area], network_and_wildcard)).start()


            # TODO 666
            self.tree.delete(item)
            # Update No
            children = self.tree.get_children()
            for i, child in enumerate(children, start=1):
                self.tree.item(child, values=(i,) + self.tree.item(child, 'values')[1:])

        buttonFrame = tk.Frame(root)
        btnAdd = tk.Button(buttonFrame, text='Add', command=lambda: add_network(router, area, self))
        btnAdd.pack()
        btnRemove = tk.Button(buttonFrame, text='Remove', command=remove_network)
        btnRemove.pack()
        btnQuit = tk.Button(buttonFrame, text='Quit', command=root.destroy)
        btnQuit.pack()
        buttonFrame.grid(column=0, row=4, columnspan=2)

        root.mainloop()

    def insert_network(self, network: Network):
        last_item = self.tree.get_children()[-1]
        last_index = self.tree.index(last_item)
        no = last_index + 2
        values = (no, network.network, network.mask)
        # Update tree
        self.tree.insert('', tk.END, values=values)
