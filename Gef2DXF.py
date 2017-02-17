from Gef2Open import Gef2OpenClass
import ezdxf


class Gef2DXF:
    def __init__(self, a_gef_file):

        # Read Gef
        self.gef = Gef2OpenClass()
        self.gef.read_gef(a_gef_file)

        # Init DXF writer
        # Documentation: http://ezdxf.readthedocs.io/en/latest/
        self.drawing = ezdxf.new(dxfversion='AC1024')
        # drawing.layers.new(name='MyLines', dxfattribs={'linetype': 'SOLID', 'color':7})
        self.modelspace = self.drawing.modelspace()

    def draw_graph_line(self, i_kol, place_left=False, value_factor=1, depth_factor=1):

        # Change depth factor to negative for drawing underground
        depth_factor *= -1

        # Add Layer for valuetype
        layername = self.gef.get_column_info(i_kol)[2]
        if not layername in self.drawing.layers:
            self.drawing.layers.new(name=layername)

        points = list()
        value_prev = 0

        for depth, value in self.gef.get_data_iter(i_kol):
            # Replace None with previous value for missing data
            if value is None:
                value = value_prev
            else:
                value_prev = value

            # Change value to negative for left hand drawing
            if place_left:
                value *= -1

            points.append((value * value_factor, depth * depth_factor))

        self.modelspace.add_polyline2d(points, dxfattribs={'layer': layername})

    def draw_vertical_ax(self, place_left=False, depth_factor=1, offset_value=1, label_height=0.2):

        # Change depth factor to negative for drawing underground
        depth_factor *= -1

        # Get max scan depth
        last_scan = int(self.gef.get_nr_scans())
        max_depth = self.gef.get_data(1, last_scan)

        self.modelspace.add_line((0, 0), (0, max_depth * depth_factor))

        for label_value in range(0, int(max_depth) + offset_value, offset_value):
            text = self.modelspace.add_text(label_value, dxfattribs={'height': label_height})
            text.set_pos((0, label_value * depth_factor), align='MIDDLE_LEFT')

    def save_drawing(self):
        self.drawing.saveas('c:/sd/gef2open/test.dxf')


if __name__ == '__main__':
    # This is used for debugging. Using this separated structure makes it much
    # easier to debug using standard Python development tools.

    myGef2DXF = Gef2DXF('GEFTEST01.gef')
    myGef2DXF.draw_graph_line(2, value_factor=0.5)  # Puntdruk MPa
    myGef2DXF.draw_graph_line(3, value_factor=2)  # Lokale wrijving MPa
    myGef2DXF.draw_graph_line(4, value_factor=2)  # Waterdruk schouder MPa
    myGef2DXF.draw_graph_line(5, place_left=True)
    myGef2DXF.draw_graph_line(6, place_left=True)
    myGef2DXF.draw_vertical_ax()

    myGef2DXF.save_drawing()
