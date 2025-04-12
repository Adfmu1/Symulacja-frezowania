from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Trsf, gp_Dir, gp_Ax2, gp_Circ
from OCC.Core.Geom import Geom_Circle
from OCC.Core.GeomAdaptor import GeomAdaptor_Curve
from OCC.Core.GCPnts import GCPnts_UniformAbscissa
from OCC.Core.Quantity import (
    Quantity_Color,
    Quantity_NOC_YELLOW,
    Quantity_NOC_CYAN,
    Quantity_NOC_GRAY75,
    Quantity_TOC_RGB  
)
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder
from OCC.Core.TopLoc import TopLoc_Location
from OCC.Display.SimpleGui import init_display
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Cut
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
from function_occ import GCodeParser
import time
import math
from OCC.Core.GeomAbs import GeomAbs_Shape
import numpy as np

class GCodeVisualizer:
    def __init__(self, height, length, width):
        self.display, self.start_display, self.add_menu, self.close = init_display()
        self.parser = GCodeParser()
        
        self.workpiece = None
        self.tool = None
        self.trail_points = []
        self.trail_shape = None
        self.feedrate = 1000
        self.last_position = gp_Pnt(0, 0, 5)
        self.trail_segments = []
        self.current_workpiece_shape = None 
        self.tool_shape = None        
        self.workpiece_ais = None        
        self.workpiece_color = None 
        self.workpiece_transparency = None
        
        self._init_workpiece(height, width, length)
        self._init_tool(2.0, 10)
        self._init_view()

    def _init_view(self):
        self.display.View.SetBgGradientColors(
            Quantity_Color(1.0, 1.0, 1.0, Quantity_TOC_RGB),
            Quantity_Color(1.0, 1.0, 1.0, Quantity_TOC_RGB),
            2, True
        )
        self.display.View.FitAll()

    def _init_workpiece(self, length, width, height):
        from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
        from OCC.Core.gp import gp_Trsf, gp_Vec
        
        box = BRepPrimAPI_MakeBox(length, width, height).Shape()
        
        translation = gp_Trsf()
        translation.SetTranslation(gp_Vec(0, 0, -height))
        box = box.Moved(TopLoc_Location(translation))
        
        self.workpiece = self.display.DisplayShape(
            box,
            color=Quantity_Color(Quantity_NOC_GRAY75),
            transparency=0.6
        )[0]
        
        self.workpiece_shape = box
        self.current_workpiece_shape = box
        self.workpiece_color = Quantity_Color(Quantity_NOC_GRAY75)
        self.workpiece_transparency = 0.6
        self.workpiece_ais = self.display.DisplayShape(
            box, 
            color=self.workpiece_color,
            transparency=self.workpiece_transparency
        )[0]

    def _init_tool(self, radius, length):
        cylinder = BRepPrimAPI_MakeCylinder(radius, length).Shape()
        self.tool = self.display.DisplayShape(
            cylinder, 
            color=Quantity_Color(Quantity_NOC_CYAN),
            transparency=0.3
        )[0]
        
        self._update_tool_position(self.last_position)
        
        self.tool_radius = radius
        self.tool_length = length
        self.tool_shape = BRepPrimAPI_MakeCylinder(radius, length).Shape()

    def _update_tool_position(self, new_pos):
        trsf = gp_Trsf()
        trsf.SetTranslation(gp_Vec(gp_Pnt(0,0,0), new_pos))
        location = TopLoc_Location(trsf)
        self.display.Context.SetLocation(self.tool, location)

    def _update_trail(self, new_pos):
        from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge
        
        if len(self.trail_points) >= 1:
            last_pnt = self.trail_points[-1]
            
            if (last_pnt.Distance(new_pos) > 1e-6):
                edge_builder = BRepBuilderAPI_MakeEdge(last_pnt, new_pos)
                if edge_builder.IsDone():
                    edge = edge_builder.Edge()
                    segment = self.display.DisplayShape(
                        edge, 
                        color=Quantity_Color(Quantity_NOC_YELLOW),
                        update=False
                    )[0]
                    self.trail_segments.append(segment)
                else:
                    print(f"Ostrzeżenie: Nie udało się utworzyć śladu między {last_pnt} a {new_pos}")
        
        self.trail_points.append(new_pos)

    def change_tool(self, new_radius):
        if self.tool is not None:
            self.display.Context.Remove(self.tool, True)
        
        current_length = self.tool_length
        
        self._init_tool(new_radius, current_length)
        
        self._update_tool_position(self.last_position)
        
    def g00(self, x, y, z):
        target = gp_Pnt(x, y, z)
        vec = gp_Vec(self.last_position, target)
        distance = vec.Magnitude()
        
        steps = max(5, int(distance * 0.5))
        
        for i in range(steps):
            t = i / steps
            current = self.last_position.Translated(vec * t)
            self._update_tool_position(current)
            self._update_trail(current)
            time.sleep(0.01)
            self.display.View.Redraw()
        
        self.last_position = target

    def g01(self, x, y, z):
        target = gp_Pnt(x, y, z)
        vec = gp_Vec(self.last_position, target)
        distance = vec.Magnitude()
        time_total = (distance / self.feedrate) * 60
        steps = max(10, int(distance * 2))

        for i in range(steps):
            t = i / steps
            current = self.last_position.Translated(vec * t)
            self._update_tool_position(current)
            self._update_trail(current)

            if current.Z() <= 0:
                trsf = gp_Trsf()
                trsf.SetTranslation(gp_Vec(current.X(), current.Y(), current.Z()))
                moved_tool = BRepBuilderAPI_Transform(self.tool_shape, trsf).Shape()
                cut = BRepAlgoAPI_Cut(self.current_workpiece_shape, moved_tool)

                if cut.IsDone():
                    self.current_workpiece_shape = cut.Shape()
                    self.display.Context.Remove(self.workpiece_ais, False)
                    self.workpiece_ais = self.display.DisplayShape(
                        self.current_workpiece_shape,
                        color=self.workpiece_color,
                        transparency=self.workpiece_transparency
                    )[0]

            time.sleep(time_total / steps)
            self.display.View.Redraw()

        self.last_position = target
    
    def g02_g03(self, params):
        center = gp_Pnt(params['center'][0], params['center'][1], params['center'][2])
        radius = params['radius']
        start_angle = params['start_angle']
        end_angle = params['end_angle']
        steps = params['steps']
        is_cw = params['is_cw']

        angular_dist = end_angle - start_angle
        angles = np.linspace(start_angle, start_angle + angular_dist, steps)

        for angle in angles:
            x = center.X() + radius * math.cos(angle)
            y = center.Y() + radius * math.sin(angle)
            z = self.last_position.Z()
            
            current_pos = gp_Pnt(x, y, z)
            self._update_tool_position(current_pos)
            self._update_trail(current_pos)

            if current_pos.Z() <= 0:
                trsf = gp_Trsf()
                trsf.SetTranslation(gp_Vec(current_pos.X(), current_pos.Y(), current_pos.Z()))
                moved_tool = BRepBuilderAPI_Transform(self.tool_shape, trsf).Shape()
                
                cut = BRepAlgoAPI_Cut(self.current_workpiece_shape, moved_tool)
                
                if cut.IsDone():
                    self.current_workpiece_shape = cut.Shape()
                    self.display.Context.Remove(self.workpiece_ais, False)
                    self.workpiece_ais = self.display.DisplayShape(
                        self.current_workpiece_shape,
                        color=self.workpiece_color,
                        transparency=self.workpiece_transparency
                    )[0]

            self.display.View.Redraw()
            time.sleep(0.01)
        
        self.last_position = current_pos
        self.display.View.FitAll()