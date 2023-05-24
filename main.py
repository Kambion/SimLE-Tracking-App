import random
import threading
import time
import serial
import aprslib
import dash
from dash import html, dcc
import dash_leaflet as dl
from dash_extensions.javascript import assign

from dash.dependencies import Input, Output

CALLSIGN = 'SR0FLY'
PORT = 'COM2'


positions = []
semaphore = threading.Semaphore(1)


# Create example app.
app = dash.Dash(prevent_initial_callbacks=True, title="SimLE Tracking App")

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <script src=\"https://kit.fontawesome.com/68ce9fd520.js\" crossorigin=\"anonymous\"></script>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

balloon_icon={"iconUrl": app.get_asset_url('balloon.png'), "iconSize": (40,40), 'iconAnchor':(20,20)}
layerGroup = dl.LayerGroup(id="container", children=[])
map = dl.Map([dl.TileLayer(), dl.LocateControl(options={'locateOptions': {'enableHighAccuracy': True},
                                                        'keepCurrentZoomLevel': True, 'icon': 'fa-solid fa-arrows-to-dot'}), layerGroup],
           center=(53.59641833454492, 19.551308688981702), zoom=8, style={'width': '100%', 'height': '100vh',
                                                                          'margin': "auto", "display": "block",
                                                                          'z-index': '0'},  id="map")



logo = html.Img(src='assets/logo.png', style={'width': '150px', 'height': '150px', 'position': 'fixed',
                                              'z-index': '2', 'top': '30px', 'right': '30px'})

app.layout = html.Div(
    children=[map,
              logo,
            dcc.Interval(
                id='interval-component',
                interval=5000,  # Update every 5 seconds
                n_intervals=0
        )
    ]
)


@app.callback(Output('container', 'children'), [Input('interval-component', 'n_intervals')])
def update_map(n):
    # Generate random coordinates for the marker
    semaphore.acquire()
    path = dl.Polyline(
        positions=positions,
        color='green',
        weight=2,
        opacity=1
    )
    children = [path]
    if len(positions) > 0:
        point = positions[-1]
        marker = dl.Marker(position=point, children=[
            dl.Tooltip(f"Lat: {point[0]}, Lon: {point[1]}")
        ], icon=balloon_icon)
        children.append(marker)
    semaphore.release()
    # Return the marker as the new children of the LayerGroup
    return children


def thread_function():
    while(True):
        ser = serial.Serial()
        ser.baudrate = 9600
        ser.port = PORT
        ser.open()
        message = str(ser.readline())
        start = message.find("PID=F0")+7
        if(message[start:].find(CALLSIGN) != -1):
            continue
        frame = CALLSIGN + ">NOCALL:" + message[start:]
        frame = aprslib.parse(frame)
        print(str(frame['latitude']) + " " + str(frame['longitude']))
        lat = frame['latitude']
        lon = frame['longitude']
        # Create a marker with the generated coordinates
        semaphore.acquire()
        positions.append([lat, lon])
        semaphore.release()
        print("Appended")


if __name__ == '__main__':
    x = threading.Thread(target=thread_function)
    x.start()
    app.run()
