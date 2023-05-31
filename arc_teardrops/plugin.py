# Arc teardrops plugin for KiCad 7
# https://github.com/sevmeyer/kicad-arc-teardrops

import os
import pcbnew
import wx

from .teardrops import addArcTeardrops


class Plugin(pcbnew.ActionPlugin):
    # https://docs.kicad.org/doxygen-python-nightly/namespacepcbnew.html

    def defaults(self):
        self.name = "Arc teardrops"
        self.description = "Add arc teardrops to all selected pads."
        self.show_toolbar_button = True
        self.icon_file_name = os.path.join(os.path.dirname(__file__), "icon.svg")
        self.dark_icon_file_name = os.path.join(os.path.dirname(__file__), "icon-dark.svg")

    def Run(self):
        parent = wx.FindWindowByName("PcbFrame")
        with Dialog(parent) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                count = addArcTeardrops(
                    max(0, min(float(dialog.radiusPTH.GetValue())/100, 10)),
                    max(0, min(float(dialog.radiusSMD.GetValue())/100, 10)),
                    max(0, min(float(dialog.radiusVIA.GetValue())/100, 10)))
                wx.MessageBox(f"Added {count} arcs", "Arc teardrops", parent=parent)


class Dialog(wx.Dialog):
    # https://docs.wxpython.org/wx.Dialog.html
    # https://docs.wxwidgets.org/stable/overview_sizer.html

    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, title="Arc teardrops")

        message = wx.StaticText(self, label=
            "Add arc teardrops to all selected pads.\n"
            "The arc radius is relative to the track width.\n"
            "A radius of 0% skips the respective pad type.")

        textPTH = wx.StaticText(self, label="PTH arc radius:")
        textSMD = wx.StaticText(self, label="SMD arc radius:")
        textVIA = wx.StaticText(self, label="Via arc radius:")

        self.radiusPTH = wx.TextCtrl(self, value="250", style=wx.TE_RIGHT)
        self.radiusSMD = wx.TextCtrl(self, value="250", style=wx.TE_RIGHT)
        self.radiusVIA = wx.TextCtrl(self, value="350", style=wx.TE_RIGHT)

        unitPTH = wx.StaticText(self, label="%")
        unitSMD = wx.StaticText(self, label="%")
        unitVIA = wx.StaticText(self, label="%")

        rootSizer = wx.BoxSizer(wx.VERTICAL)
        inputSizer = wx.FlexGridSizer(3)
        buttonSizer = self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL)

        left = wx.SizerFlags().Left()
        right = wx.SizerFlags().Right().Border(wx.RIGHT)
        center = wx.SizerFlags().Centre().Border(wx.ALL)

        inputSizer.AddMany((
            (textPTH, right), (self.radiusPTH, right), (unitPTH, left),
            (textSMD, right), (self.radiusSMD, right), (unitSMD, left),
            (textVIA, right), (self.radiusVIA, right), (unitVIA, left)))

        rootSizer.Add(message, center)
        rootSizer.Add(inputSizer, center)
        rootSizer.Add(buttonSizer, center)

        self.SetSizerAndFit(rootSizer)
