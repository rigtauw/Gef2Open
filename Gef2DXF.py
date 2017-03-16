from Gef2Open import Gef2OpenClass
import ezdxf


# Create a range containing decimal values
def drange(start, stop, step):
    start = int(start * 100)
    stop = int(stop * 100)
    step = int(step * 100)
    trange = range(start, stop, step)

    return [float(v) / 100 for v in trange]


class GraphExtent:
    def __init__(self):
        self._x_left = 0
        self._x_right = 0
        self._y_bottom = 0

    @property
    def x_left(self):
        return self._x_left

    @x_left.setter
    def x_left(self, value):
        if value < self._x_left:
            self._x_left = value

    @property
    def x_right(self):
        return self._x_right

    @x_right.setter
    def x_right(self, value):
        if value > self._x_right:
            self._x_right = value

    @property
    def y_bottom(self):
        return self._y_bottom

    @y_bottom.setter
    def y_bottom(self, value):
        if value < self._y_bottom:
            self._y_bottom = value


class Gef2DXF:
    def __init__(self, a_gef_file, existing_ezdxf=None):

        """
        Initialise the class
        :param a_gef_file: a gef file to be processed
        :param existing_ezdxf: a existing dwg (as ezdxf object)
        """
        self.gef = Gef2OpenClass()
        self.gef.read_gef(a_gef_file)

        # Init DXF writer
        # Documentation: http://ezdxf.readthedocs.io/en/latest/

        if existing_ezdxf is None:
            self.drawing = ezdxf.new(dxfversion='AC1024')
            # drawing.layers.new(name='MyLines', dxfattribs={'linetype': 'SOLID', 'color':7})
            self.modelspace = self.drawing.modelspace()
        else:
            self.drawing = existing_ezdxf
            self.modelspace = existing_ezdxf.modelspace()

        # Initialise drawing extent (manipulated by draw_###_ax functions)
        self.extent = GraphExtent()

    def draw_graph_line(self, i_kol, value_factor, depth_factor, place_left=False):
        """
        Draw a vertical graph_line
        :param i_kol: index of column in GEF file
        :param value_factor: scale factor for plotting values
        :param depth_factor: scale factor for plotting depth
        :param place_left: place left of central Y-axis if TRUE
        """

        # Change depth factor to negative for drawing underground
        depth_factor *= -1

        # Add Layer for valuetype
        layername = self.gef.get_column_info(i_kol)[2]
        if layername not in self.drawing.layers:
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

    def draw_vertical_ax(self, depth_factor, offset_value, label_height=0.2):
        """
        Draw a vertical central positioned vertical axis with depth labels
        :param depth_factor: scale factor for plotting depth
        :param offset_value: value defining the separation between the depth labels
        :param label_height: label height in map units
        """
        # Change depth factor to negative for drawing underground
        depth_factor *= -1

        # Get max scan depth
        last_scan = int(self.gef.get_nr_scans())
        max_depth = self.gef.get_data(1, last_scan)

        # Add Layer for valuetype
        layername = 'Axis'
        if layername not in self.drawing.layers:
            self.drawing.layers.new(name=layername)

        # Add vertical ax line
        x1 = 0
        y1 = 0
        x2 = 0
        y2 = max_depth * depth_factor
        self.modelspace.add_line((x1, y1), (x2, y2), dxfattribs={'layer': layername})

        # Add labels
        for label_value in drange(0, max_depth, offset_value):
            text = self.modelspace.add_text(label_value, dxfattribs={'layer': layername, 'height': label_height})
            x = 0
            y = label_value * depth_factor
            text.set_pos((x, y), align='TOP_LEFT')

        # Update extent
        self.extent.y_bottom = y2

    def draw_horizontal_ax(self, i_kol, max_value, offset_value, value_factor, place_left=False, place_bottom=False,
                           depth_factor=1, label_height=0.2):

        """
        Draw a horizontal axis with value labels, positioned at top/bottom and left/right
        :param i_kol: index of column in GEF file
        :param max_value: value defining the maximum value of the horizontal ax
        :param offset_value: value defining the separation between the value labels
        :param value_factor: scale factor for plotting values
        :param place_left: place left of central Y-axis if TRUE
        :param place_bottom:  place at bottom of graph if TRUE
        :param depth_factor: scale factor for plotting depth (when place_bottom = TRUE)
        :param label_height: label height in map units
        """

        # Add Axis Layer for value type
        layername = self.gef.get_column_info(i_kol)[2] + " Axis"
        if layername not in self.drawing.layers:
            self.drawing.layers.new(name=layername)

        # Change values to negative for left hand drawing
        if place_left:
            max_value *= -1
            offset_value *= -1

        # Change depth factor to negative for drawing underground
        depth_factor *= -1

        # Calculate depth for placement on bottom of graph
        if place_bottom:
            # Get max scan depth
            last_scan = int(self.gef.get_nr_scans())
            ax_depth = self.gef.get_data(1, last_scan)
        else:
            ax_depth = 0

        # Define text alignment
        if place_left and place_bottom:
            text_align = 'TOP_RIGHT'
        elif place_left and not place_bottom:
            text_align = 'BOTTOM_RIGHT'
        elif not place_left and place_bottom:
            text_align = 'TOP_LEFT'
        elif not place_left and not place_bottom:
            text_align = 'BOTTOM_LEFT'
        else:
            raise Exception('Wrong text alignment selection.')

        # Add horizontal ax line
        x1 = 0
        y1 = ax_depth * depth_factor
        x2 = max_value * value_factor
        y2 = ax_depth * depth_factor
        self.modelspace.add_line((x1, y1), (x2, y2), dxfattribs={'layer': layername})

        # Add labels
        for label_value in drange(0, max_value + offset_value, offset_value):
            if place_left:
                label_text = abs(label_value)  # remove negative sign
            else:
                label_text = label_value
            text = self.modelspace.add_text(label_text, dxfattribs={'layer': layername, 'height': label_height})
            x = label_value * value_factor
            y = ax_depth * depth_factor
            text.set_pos((x, y), align=text_align)

        if place_left:
            self.extent.x_left = x2
        else:
            self.extent.x_right = x2

    def draw_raster(self, value_factor, offset_value):

        # Add layer for raster
        """
        Draw a horizontal and vertical background raster based on the offset from the x and y axis
        :param value_factor: scale factor for plotting the raster lines
        :param offset_value: value defining the separation between the raster lines
        """
        layername = 'Raster'
        if layername not in self.drawing.layers:
            self.drawing.layers.new(name=layername, dxfattribs={'color': 1})

        range_x_left = drange(0, self.extent.x_left, value_factor * offset_value * -1)
        range_x_right = drange(0, self.extent.x_right, value_factor * offset_value)
        range_y_bottom = drange(0, self.extent.y_bottom, value_factor * offset_value * -1)

        # Horizontal lines
        for y in range_y_bottom[1:-1]:
            self.modelspace.add_line((self.extent.x_left, y), (self.extent.x_right, y), dxfattribs={'layer': layername})

        # Vertical lines left
        for x in range_x_left[1:]:
            self.modelspace.add_line((x, 0), (x, self.extent.y_bottom), dxfattribs={'layer': layername})

        # Vertical lines right
        for x in range_x_right[1:]:
            self.modelspace.add_line((x, 0), (x, self.extent.y_bottom), dxfattribs={'layer': layername})

    def save_drawing(self, path):
        """
        Save the created drawing to a DXF file
        :param path: file path
        """
        self.drawing.saveas(path)


if __name__ == '__main__':
    # This is used for debugging. Using this separated structure makes it much
    # easier to debug using standard Python development tools.

    myGef2DXF = Gef2DXF('GEFTEST01.gef')

    # Left up
    myGef2DXF.draw_graph_line(i_kol=2, value_factor=0.4, depth_factor=1, place_left=True)  # Puntdruk MPa
    myGef2DXF.draw_horizontal_ax(i_kol=2, max_value=30, offset_value=5, value_factor=0.4,
                                 place_left=True)  # Puntdruk MPa

    # Left down
    myGef2DXF.draw_graph_line(i_kol=3, value_factor=20, depth_factor=1, place_left=True)  # Lokale wrijving MPa
    myGef2DXF.draw_horizontal_ax(i_kol=3, max_value=0.5, offset_value=0.1, value_factor=20, place_left=True,
                                 place_bottom=True, depth_factor=1)  # Lokale wrijving MPa

    # Right up
    myGef2DXF.draw_graph_line(i_kol=6, value_factor=1, depth_factor=1)  # Wrijvingsgetal
    myGef2DXF.draw_horizontal_ax(i_kol=6, max_value=12, offset_value=2, value_factor=1)  # Wrijvingsgetal

    # Right down
    myGef2DXF.draw_graph_line(i_kol=4, value_factor=20, depth_factor=1)  # Waterdruk schouder MPa
    myGef2DXF.draw_horizontal_ax(i_kol=4, max_value=0.5, offset_value=0.1, value_factor=20,
                                 place_bottom=True, depth_factor=1)  # Waterdruk schounder MPa

    myGef2DXF.draw_vertical_ax(depth_factor=1, offset_value=1)

    myGef2DXF.draw_raster(value_factor=1, offset_value=1)
    myGef2DXF.save_drawing('c:/sd/gef2open/test.dxf')
