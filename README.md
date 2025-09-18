# OSM PT Routing Plugin

## Overview
This QGIS plugin enables advanced routing analysis for public transport systems by leveraging processed OpenStreetMap (OSM) data and GTFS (General Transit Feed Specification) datasets. It is designed to work seamlessly with other plugins in the series to provide comprehensive spatial analysis and routing capabilities.

## Features
- **Public Transport Routing**: Calculates optimal routes using OSM road networks and GTFS stop data.
- **Integration with OSM and GTFS**: Utilizes spatial attributes from OSM and GTFS for accurate routing.
- **Customizable Routing Parameters**: Supports various transport modes and user-defined preferences.
- **Layer Generation**: Produces layers optimized for routing and visualization in QGIS.

## Teasing
Watch the teasing for these plugin [here](https://drive.google.com/file/d/1LilcjYFtBTateYkhFQe7UMBH2HwEt9Wo/view?usp=drive_link).

## FlowRide Plugin Series
This plugin is the third in a series of four plugins for public transport analysis:
1. **GTFS Agency Selection** ([GitHub Repository](https://github.com/skagejj/gtfsagency_selection)): Select and filter GTFS data for specific agencies.
2. **OSM Import Roads and Public Transport Stops** ([GitHub Repository](https://github.com/skagejj/OSMimport_roads_PTstops)): Import and integrate OSM road and stop data with GTFS datasets.
3. **OSM PT Routing** (This Plugin): Perform advanced routing using processed OSM and GTFS data.
4. **GTFS Shapes Tracer** ([GitHub Repository](https://github.com/skagejj/gtfs_shapes_tracer)): Generate GTFS shapes for route visualization.

## Usage
0. **Prepare Data**: Use the previous plugins to import and process OSM and GTFS data.
1. **Find and move the off-road stops**: with the "Download the separate PT stops" button you can detect the stops, those need to be moved
2. **Run Routing Analysis**: Use OSM PT Routing to calculate and visualize public transport routes.
3. **Visualize Results**: Display optimized routes and layers in QGIS for further analysis.

## Video Tutorial
Watch the video tutorial for this plugin [here](https://drive.google.com/file/d/1LjzkYpu6Bfrb2KlrN3byfVHU8qHSqKoH/view?usp=sharing).

## Installation
1. Clone or download the plugin repository.
2. Place the plugin folder in your QGIS plugins directory:
   ```
   c:\Users\<your_username>\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\
   ```
3. Restart QGIS and enable the plugin from the Plugin Manager.

## Dependencies
- QGIS 3.x
- Python libraries: `pandas`, `numpy`, `statistics`
- QGIS Processing Toolbox
- QuickOSM

## License
This plugin is distributed under the GNU General Public License v2.0 or later.

## Author
Luigi Dal Bosco  
Email: luigi.dalbosco@gmail.com  
Generated using [QGIS Plugin Builder](http://g-sherman.github.io/Qgis-Plugin-Builder/).
