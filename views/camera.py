#!/usr/bin/env python
# -*- coding: utf-8 -*-
from traits.api import*
from traitsui.api import*
from traitsui.menu import OKButton, CancelButton
from chaco.api import Plot, ArrayPlotData
from chaco.tools.api import PanTool, ZoomTool
from enable.component_editor import ComponentEditor
import thread
import time
from ctypes import *

import controls.camera
reload (controls.camera)
import views.cryo

from pyface.api import error,warning,information

class CameraGUI(HasTraits):
    camera=controls.camera.Camera()

    acq_active = False
    toggle_active = False

    simulate_camera=Bool(True)
    cooler=Bool(False)
    single=Button()
    continous=Button()
    autofocus=Button(label="AF")
    settemperature=Range(low=-70,high=20,value=20)

    x_step = Float(0.1)
    y_step = Float(0.1)
    icryo = Instance(views.cryo.CryoGUI)

    """menu"""
    readmode=Int(0)
    acquisitionmode=Int(1)
    exposuretime=Range(low=0.0001,high=10,value=0.1,editor=TextEditor(evaluate=float,auto_set=False))
    Vshiftspeed = Enum(1,2,3)
    Hshiftspeed = Enum(1,2,3)

    output=Str()
    plot = Instance(Plot,())


#    view_menu=View(HGroup(VGroup(
#                        HGroup(Item('single',show_label=False), Item('plot',show_label=False)),
#                        Item('settemperature'),
#                        HGroup(Item('cooler'),Item('simulate_camera',label='Simulation camera')),
#                        HGroup(Item('output',label='Camera output',
#                            style='readonly')),
#                        VGroup(Item('readmode'),Item('acquisitionmode'),Item('exposuretime'))
#                        ),
#                        Item('plot',editor=ComponentEditor(size=(200,200)),show_label=False)),
#                        resizable = True )
#
    menu_action = Action(name='camera menu', accelerator='Ctrl+p', action='call_menu')
    mi_reload = Action(name='reload camera module', accelerator='Ctrl+r',
            action='reload_camera')

    menu=Menu(menu_action,mi_reload,name='Camera')

    readmodes = Enum('Full Vertical Binning','Image')
            #SetReadMode(0)

            #SetReadMode(4);
            #SetImage(1,1,1,1024,1,256);

#GetNumberHSSpeeds(0, 0, &a); //first A-D, request data speeds for (I = 0; I <
#        a;I++)
#GetHSSpeed(0, 0, I, &speed[I]);
#SetHSSpeed(0, 0); /* Fastest speed */

    continous_label = Str('Continous')


    traits_view=View(HGroup(VGroup(
                        HGroup(Item('single',label='Single',show_label=False),
                               Item('continous',show_label=False,editor=ButtonEditor(label_value
= 'continous_label')),Item('autofocus',show_label=False)),
                        HGroup(Item('exposuretime'),Item('simulate_camera',label='simulate camera')),
                        Item('readmodes'),
                        Item('Vshiftspeed'),
                        Item('Hshiftspeed')
                       ),
                       Item('plot',editor=ComponentEditor(size=(200,200)),show_label=False)),
                       resizable = True, menubar=MenuBar(menu) )

    def _single_fired(self):
            try:
                self.line=self.camera.acquisition(sim_pos=self.icryo.cryo.pos())
            except: 
                self.line=self.camera.acquisition()
            self.plot_data()

    def _autofocus_fired(self):
        xtest = False
        ytest = False
        try:
            self.line=self.camera.acquisition(sim_pos=self.icryo.cryo.pos())
        except:
            self.line=self.camera.acquisition()

        while xtest == False: #Test in die x-Richtung, suchen bis Counts runter
            a = max(self.line)
            self.icryo.cryo.rmove(self.x_step,0)
            try:
                self.line=self.camera.acquisition(sim_pos=self.icryo.cryo.pos())
            except:
                self.line=self.camera.acquisition()
            self.plot_data()
            b = max(self.line)
            if b < a:
                self.icryo.cryo.rmove(-self.x_step,0)
                try: #damit er wieder das aktuelle max hat
                    self.line=self.camera.acquisition(sim_pos=self.icryo.cryo.pos())
                except:
                    self.line=self.camera.acquisition()
                xtest = True

        xtest=False

        while xtest == False: #Test in die -x-Richtung, suchen bis Counts runter
            a = max(self.line)
            self.icryo.cryo.rmove(-self.x_step,0)
            try:
                self.line=self.camera.acquisition(sim_pos=self.icryo.cryo.pos())
            except:
                self.line=self.camera.acquisition()
            self.plot_data()
            b = max(self.line)
            if b < a:
                self.icryo.cryo.rmove(self.x_step,0)
                try:
                    self.line=self.camera.acquisition(sim_pos=self.icryo.cryo.pos())
                except:
                    self.line=self.camera.acquisition()
                xtest = True

        while ytest == False: #Test in die y-Richtung, suchen Counts runter
           a = max(self.line)
           self.icryo.cryo.rmove(0,self.y_step)
           try:
                self.line=self.camera.acquisition(sim_pos=self.icryo.cryo.pos())
           except:
                self.line=self.camera.acquisition()
           self.plot_data()
           b = max(self.line)
           if b < a:
                self.icryo.cryo.rmove(0,-self.y_step)
                try:
                    self.line=self.camera.acquisition(sim_pos=self.icryo.cryo.pos())
                except:
                    self.line=self.camera.acquisition()
                ytest = True

        ytest = False

        while ytest == False: #Test in die -y-Richtung, suchen Counts runter
           a = max(self.line)
           self.icryo.cryo.rmove(0,-self.y_step)
           try:
                self.line=self.camera.acquisition(sim_pos=self.icryo.cryo.pos())
           except:
                self.line=self.camera.acquisition()
           self.plot_data()
           b = max(self.line)
           if b < a:
                self.icryo.cryo.rmove(0,self.y_step)
                try:
                    self.line=self.camera.acquisition(sim_pos=self.icryo.cryo.pos())
                except:
                    self.line=self.camera.acquisition()
                ytest = True

        self.plot_data()
        print "AF fertig!"


    def plot_data(self):
        plotdata = ArrayPlotData(x=self.line[:])
        plot = Plot(plotdata)
        plot.plot(("x"),  color="blue")
        plot.title = ""
        plot.overlays.append(ZoomTool(component=plot,tool_mode="box", always_on=False))
        plot.tools.append(PanTool(plot, constrain_key="shift"))
        #plot.tools.append(PlotTool(component=plot))
        #plot.range2d.x_range.low=self.x1
        #plot.range2d.x_range.high=self.x2
        #plot.range2d.y_range.low=self.y1
        #plot.range2d.y_range.high=self.y2
        plot.x_axis.title="x-Position on sample [mm]"
        plot.y_axis.title="y-Position on sample [mm]"
        self.plot=plot

    def ensure_init(self):
        if self.camera.init_active:
            information(parent=None, title="please wait", message="The initialization of the camera is running. Please wait until the initialization is finished.")
            while self.camera.init_active:
                time.sleep(.5)


    def _settemperature_changed(self):
        self.ensure_init()
        self.camera.settemperature(self.settemperature)

    def _simulate_camera_changed(self):
        self.stop_acq_thread()
        # wenn es nicht schon läuft, schicke self.toggle_simulate() in den
        # Hintergrund
        if not self.toggle_active:
            self.toggle_active = True
            thread.start_new_thread(self.toggle_simulation,())

    def toggle_simulation(self):
        # camera.toggle_simulation() liefert simulieren = True/False zurück
        self.simulate_camera = self.camera.toggle_simulation()
        self.toggle_active = False

    def acq_thread(self):
        self.continous_label = 'Stop'
        while self.acq_active:
            self._single_fired()
        self.continous_label = 'Continous'

    def _continous_fired(self):
        self.acq_active = not self.acq_active
        if self.acq_active:
            thread.start_new_thread(self.acq_thread,())

    def _cooler_changed(self):
        if self.cooler:
            self.camera.cooler_on()
        else:
            self.camera.cooler_off()

    def _readmode_changed(self):
       self.camera.readmode=c_long(self.readmode)
       print "readmode changed"

    def _acquisitionmode_changed(self):
       self.camera.acquisitionmode=c_long(self.acquisitionmode)
       print "acq mode changed"

    def _exposuretime_changed(self):
       self.camera.exposuretime=c_float(self.exposuretime)
       print "exp changed"

    def call_menu(self):
       self.configure_traits(view='view_menu')

    def reload_camera(self):
        import pdb; pdb.set_trace()


    def stop_acq_thread(self):
        if self.acq_active:
            self.acq_active = False
            while self.continous_label == 'Stop':
                time.sleep(0.1)

    def close(self):
        self.stop_acq_thread()
        self.camera.close()

if __name__=="__main__":
    main=CameraGUI(icryo = views.cryo.CryoGUI())
    main.configure_traits()
    main.close()
