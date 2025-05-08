# Plot OISST for the Bay of Bengal (EKAMSAT 2025 cruise)
#

# %%
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import xarray as xr
import cartopy.crs as ccrs                   # import projections
import cartopy
import geopandas as gpd # for the EEZ shapefile
import functions_Debarshi
import pandas as pd

# %%
# Change to this directory
home_dir = os.path.expanduser("~")

# To work for Tom and other people
if os.path.exists(home_dir + '/Python/EKAMSAT_2025_cruise/src'):
    os.chdir(home_dir + '/Python/EKAMSAT_2025_cruise/src')

# %%
# %matplotlib inline
#%matplotlib widget
# %matplotlib qt5
plt.rcParams['figure.figsize'] = (6,6)
plt.rcParams['figure.dpi'] = 100
plt.rcParams['savefig.dpi'] = 400

savefig = True # set to true to save plots as file

__figdir__ = '../img/SST_movie/'
sst_figdir = '../img/SST_movie/'
os.system('mkdir  -p ' + __figdir__) #make directory if it doesn't exist
savefig_args = {'bbox_inches':'tight', 'pad_inches':0.2}
kml_savefig_args = {'bbox_inches':'tight', 'pad_inches':0, 'transparent':True}
plotfiletype='png'

# %%
# clear the directory
#os.system('rm -f ' + __figdir__ + '*')


# %%
# Download the data if needed
# https://psl.noaa.gov/thredds/catalog/Datasets/noaa.oisst.v2.highres/catalog.html?dataset=Datasets/noaa.oisst.v2.highres/sst.day.mean.2023.nc

# download the data to ../data/external if it does not already exist there
data_dir = '../data/external'
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

#url = 'https://psl.noaa.gov/thredds/fileServer/Datasets/noaa.oisst.v2.highres/sst.day.mean.2023.nc'
url = 'https://psl.noaa.gov/thredds/fileServer/Datasets/noaa.oisst.v2.highres/sst.day.mean.2025.nc'


filename = os.path.join(data_dir, os.path.basename(url))
if not os.path.exists(filename):
    import urllib.request
    urllib.request.urlretrieve(url, filename)
else: # check if the file is older than 0.5 days
    # Get the last modified time of the file
    import datetime
    import time
    import urllib.request
    # Get the last modified time of the file
    last_modified_time = os.path.getmtime(filename)
    # Convert the last modified time to a human-readable format
    last_modified_time = datetime.datetime.fromtimestamp(last_modified_time)
    print("Last modified time:", last_modified_time)
    print("Time now:", datetime.datetime.now())
    # compute age of file:
    age = datetime.datetime.now() - last_modified_time
    print("Age of file:", age)
    # If the file is older than 0.5 days, download it again
    if age.total_seconds() > 43200:  # 0.5 days in seconds
        print("File is older than 0.5 days, downloading again")
        urllib.request.urlretrieve(url, filename)



# %%
#Load waypoints

# Nominal location: 7°57'47.83" N  87°38'25.56" E
mooring = dict(
    lon = [86],
    lat = [12])
# Load the WG-array points
import pandas as pd
df = pd.read_excel("../data/external/lat_lon_data.xlsx", sheet_name="IDA")  # Change 'Sheet1' as needed
IDA = xr.Dataset.from_dataframe(df)
df = pd.read_excel("../data/external/lat_lon_data.xlsx", sheet_name="PLANCK")  # Change 'Sheet1' as needed
PLANCK = xr.Dataset.from_dataframe(df)
df = pd.read_excel("../data/external/lat_lon_data.xlsx", sheet_name="WHOI43")  # Change 'Sheet1' as needed
WHOI43 = xr.Dataset.from_dataframe(df)
df = pd.read_excel("../data/external/lat_lon_data.xlsx", sheet_name="WHOI1102")  # Change 'Sheet1' as needed
WHOI1102 = xr.Dataset.from_dataframe(df)
# %%
# Current first survey waypoint
# OLD: wpt = dict(lon=[86 + 34.62/60], lat=[13 + 48.03/60])
#  13.875100°   86.482300°
#  13.323279°   86.501382°
#  14.466317°   88.833707°  
wpt = dict(lon=[88.83, 88.83, 86.48, 86.50, 88.83], lat=[12.33, 15, 13.87, 13.32, 14.47])
  
# Convert waypoints from decimal degrees to degrees and decimal minutes
def decimal_to_dms(value, direction_positive, direction_negative):
    degrees = int(value)
    minutes = (value - degrees) * 60
    direction = direction_positive if value >= 0 else direction_negative
    return f"{degrees}° {minutes:.2f}' {direction}"

wpt_dms = [
    f"{decimal_to_dms(lat, 'N', 'S')}, {decimal_to_dms(lon, 'E', 'W')}"
    for lat, lon in zip(wpt['lat'], wpt['lon'])
]

print("Waypoints in DMS format (lat, lon):")
for waypoint in wpt_dms:
    print(waypoint)




# %%


# Get ship position from this url:
# https://www.ocean.washington.edu/files/thompson.txt
ship_pos_url = 'https://www.ocean.washington.edu/files/thompson.txt'
ship_pos = pd.read_csv(ship_pos_url, sep=',', header=None, names=['asset', 'DD-MM-YYYY', 'HH:MM:SS', 'lat', 'lon', 'T', 'NULL1', 'NULL2', 'BPR', 'NULL3', 'NULL4', 'NULL5', 'NULL6', 'NULL7', 'NULL8', 'NULL9', 'Voyage'])
print(ship_pos.head())
latitudes = ship_pos['lat']
longitudes = ship_pos['lon']
# %%
# Load the data
ds = xr.open_dataset(filename)

# %% Shift ds to have longitude from -180 to 180
ds = ds.assign_coords(lon=(ds.lon + 180) % 360 - 180)
ds = ds.sortby(ds.lon)


# %%
zoom = False
domovie = False
if zoom:
    xmin, xmax = (80,95)
    ymin, ymax = (5,20)
else:
    xmin, xmax = (70,100)
    ymin, ymax = (0, 25)
# %%
ds_ssh = xr.open_dataset('../data/external/aviso.nc')

# %%
def add_vel_quiver(tind,ax=plt.gca()):
    if ax is None:
        ax = plt.gca()

    u = np.squeeze(ds_ssh.ugos.isel(time=tind)) #dtype=object
    v = np.squeeze(ds_ssh.vgos.isel(time=tind))
    skip = 4
    scalefac = 20
    q = ax.quiver(ds_ssh.longitude.values[::skip], ds_ssh.latitude.values[::skip], u.values[::skip,::skip], v.values[::skip,::skip], scale=scalefac, transform=ccrs.PlateCarree())
    x0 = 81.5
    y0 = 17.33
    ax.quiverkey(q,x0,y0,0.25, '0.25 m/s', zorder=3, transform=ccrs.PlateCarree())
    #ax.quiver(np.array([x0]), np.array([y0]), -np.array([0.25/np.sqrt(2)],), np.array([0.25/np.sqrt(2)]), scale=scalefac, transform=ccrs.PlateCarree(),zorder=3)
    #ax.text(x0+3/60, y0+.15/60, '0.25 m/s', fontsize=6,transform=ccrs.PlateCarree())


######################

# %%
## Plot the data
def plot_map(data, levels, title='', outfile='', savefig=False, ax=None):
    if title is None:
        title = ''
    if outfile is None:
        outfile = title
    if ax is None:
        fig, ax = plt.subplots(subplot_kw={'projection': ccrs.PlateCarree()})  # Create a new axis if none is provided
    coast = cartopy.feature.GSHHSFeature(scale="full")
    ax.add_feature(coast, zorder=3, facecolor=[.6, .6, .6], edgecolor='black')

    # Add gridlines
    gl = ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False, alpha=0.5, linestyle='--')
    gl.top_labels = False
    gl.right_labels = False

    # Add country boundaries
    ax.add_feature(cartopy.feature.BORDERS, linestyle='-', alpha=0.5, zorder=10)
    ax.add_feature(cartopy.feature.NaturalEarthFeature(category='cultural', name='admin_0_countries', scale='50m', facecolor='none'), zorder=10)
    ax.add_feature(cartopy.feature.RIVERS, edgecolor='blue', zorder=10, alpha=0.25)

    # Plot the data
    cs = ax.pcolormesh(data.lon, data.lat, data, vmin=levels[0], vmax=levels[-1], transform=ccrs.PlateCarree())
    cb = plt.colorbar(cs, ax=ax, fraction=0.022, extend='both')
    cb.set_label('SST [$\\circ$C]', fontsize=10)
    ax.axis('scaled')
    ax.set_title(title)

    # Add 2024 site
    site_2024 = ax.plot(mooring['lon'], mooring['lat'], 'o', color='k', markeredgecolor='w', markersize=8, transform=ccrs.PlateCarree(), label='2024 site')

    if savefig:
        outfile2 = outfile.replace(' ', '_')
        plt.savefig(__figdir__ + outfile2 + '.' + plotfiletype, **savefig_args)
    return ax, site_2024




# %%
# Make one plot for the last time in the file
t1 = ds.time[-1].values
fstr = t1.astype('datetime64[D]')
t1 = str(fstr)
sst = ds.sst.sel(lon=slice(xmin,xmax), lat=slice(ymin,ymax),time=t1)



# %%
levels = np.arange(29, 32, 0.1)
ax, site_2024 = plot_map(sst, levels, title='SST,' + t1, savefig=False)
# add WG pts at lat = -0.5, 0.5, 1.0 and lon =-140.5 and -139.5
# BD08: 17.817 N, 89.175 E
# BD09: 17.460 N, 89.124 E
# BD10: 16.322 N, 87.991 E
# BD13: 13.99 N, 87.00 E
# RAMA: 15.04 N, 89.04 E
# RAMA: 12.01 N, 88.51 E


BD = ['BD08', 'BD09', 'BD10', 'BD13', 'RAMA', 'RAMA']
pts_lon = [89.175, 89.124, 87.991, 87.00, 89.04, 88.51]
pts_lat = [17.817, 17.460, 16.322, 13.99, 15.04, 12.01]
plt.plot(pts_lon, pts_lat, 'o', color='m',markeredgecolor='k', markersize=8, transform=ccrs.PlateCarree(),label='BD/RAMA moorings')
plt.legend()

plt.savefig(__figdir__+'SST_WG_array_example.' +plotfiletype,**savefig_args)
# %%
# Add EEZ
# Download the file to ../data/external/
# https://www.marineregions.org/downloads.php#eez

#EEZ_file = '../data/external/World_EEZ_v12_20231025.zip'
#if not os.path.isfile(EEZ_file):
#    import urllib.request
#    url = 'https://www.marineregions.org/downloads.php#eez'
#    urllib.request.urlretrieve(url, EEZ_file)
# %%
# Unzip the file
#if not os.path.exists(data_dir + '/World_EEZ_v12_20231025'):
#    import zipfile
#    # Unzip the file
#    data_dir = '../data/external'
#    EEZ_file = data_dir + '/World_EEZ_v12_20231025.zip'
#    with zipfile.ZipFile(EEZ_file, 'r') as zip_ref:
#        zip_ref.extractall(data_dir)

# Read the shapefile
#shapefile = data_dir + '/World_EEZ_v12_20231025/eez_v12.shp'
#gdf = gpd.read_file(shapefile)
import scipy.io
mat_data = scipy.io.loadmat('../data/external/World_EEZ/eez.mat')
eez = mat_data['eez'];
eez = np.array(eez)
# %% 
# Step 1: Mount the google drive file first: It has the wave glider data
# Step 2: Copy them from the folder
directory = "../../../../mnt/g/Shared\ drives/AirSeaLab_Shared/ASTRAL_2025/PAYLOAD/MAT/";
Assets = ['IDA','PLANCK','WHOI43','WHOI1102'];
Extra = '_PLD_DATA_ALL.mat';
to_file = "../data/external/"
!cp {"../../../../../mnt/g/Shared\ drives/AirSeaLab_Shared/ASTRAL_2025/PAYLOAD/MAT/IDA_PLD_DATA_ALL.mat"} {to_file}
!cp {"../../../../../mnt/g/Shared\ drives/AirSeaLab_Shared/ASTRAL_2025/PAYLOAD/MAT/WHOI43_PLD_DATA_ALL.mat"} {to_file}
!cp {"../../../../../mnt/g/Shared\ drives/AirSeaLab_Shared/ASTRAL_2025/PAYLOAD/MAT/PLANCK_PLD_DATA_ALL.mat"} {to_file}
!cp {"../../../../../mnt/g/Shared\ drives/AirSeaLab_Shared/ASTRAL_2025/PAYLOAD/MAT/WHOI1102_PLD_DATA_ALL.mat"} {to_file}
#Step 3: Load the required variables using scipy.io
import scipy.io as sio
IDA = sio.loadmat(to_file+Assets[0]+Extra,struct_as_record=False, squeeze_me=True)
PLANCK = sio.loadmat(to_file+Assets[1]+Extra,struct_as_record=False, squeeze_me=True)
WHOI43 = sio.loadmat(to_file+Assets[2]+Extra,struct_as_record=False, squeeze_me=True)
WHOI1102 = sio.loadmat(to_file+Assets[3]+Extra,struct_as_record=False, squeeze_me=True)
# %%
# Plot the shapefile on the map
fig, ax = plt.subplots(subplot_kw={'projection': ccrs.PlateCarree()})  # Define ax with cartopy projection
plt.set_cmap(cmap=plt.get_cmap('turbo'))
levels = np.arange(29.5, 31.25, 0.25)

# Plot the SST map on the same axis
ax, site_2024 = plot_map(sst, levels, title='SST,' + t1, savefig=False, ax=ax)

# Plot the BD/RAMA moorings
bd = ax.plot(pts_lon, pts_lat, 'o', color='m', markeredgecolor='k', markersize=8, transform=ccrs.PlateCarree(), label='BD/RAMA moorings')
for i in range(len(pts_lon)):
    # label the points
    ax.text(pts_lon[i] + 0.1, pts_lat[i] + 0.1, BD[i], fontsize=12, color='c', transform=ccrs.PlateCarree(), zorder=4)

ax.plot(IDA["IDA"].PLD2_TAB1.longitude_Avg, IDA["IDA"].PLD2_TAB1.latitude_Avg, 'o', color='darkviolet', markeredgecolor='k', markersize=8, transform=ccrs.PlateCarree(), label='IDA')
ax.plot(PLANCK["PLANCK"].PLD2_TAB1.longitude_sitex_Avg, PLANCK["PLANCK"].PLD2_TAB1.latitude_sitex_Avg, 'o', color='teal', markeredgecolor='k', markersize=8, transform=ccrs.PlateCarree(), label='PLANCK')
ax.plot(WHOI43["WHOI43"].PLD2_TAB1.longitude_Avg, WHOI43["WHOI43"].PLD2_TAB1.latitude_Avg, 'o', color='deeppink', markeredgecolor='k', markersize=8, transform=ccrs.PlateCarree(), label='WHOI43')
ax.plot(WHOI1102["WHOI1102"].PLD2_TAB1.longitude_Avg, WHOI1102["WHOI1102"].PLD2_TAB1.latitude_Avg, 'o', color='olivedrab', markeredgecolor='k', markersize=8, transform=ccrs.PlateCarree(), label='WHOI1102')

# Plot the shapefile
ax.plot(eez[:,0], eez[:,1], 'w-', linewidth=1, transform=ccrs.PlateCarree(), zorder=3,label='EEZ')

ax.grid(True)

# Add titles and labels
ax.set_title('SST,' + t1)
ax.set_xlabel('Longitude')
ax.set_ylabel('Latitude')
ax.set_xlim(xmin, xmax)
ax.set_ylim(ymin, ymax)
next_wpt = plt.plot(wpt['lon'], wpt['lat'], 'o', color='r', markeredgecolor='w', markersize=8, transform=ccrs.PlateCarree(), label='Current waypoint')
tgt = plt.plot(longitudes, latitudes, 'o', color='b', markeredgecolor='w', markersize=8, transform=ccrs.PlateCarree(), label='Ship Position')
plt.legend([site_2024[0], bd[0], next_wpt[0], tgt[0]], ['2024 site', 'BD/RAMA moorings', 'Current waypoint', 'Ship Position'], loc='upper right', framealpha=0.8)

#plt.legend(framealpha=0.8)
plt.show()


tind=-1
add_vel_quiver(tind, ax=ax)

if savefig:
    outfile2 = 'SST_UV_map_' + t1.replace(' ', '_')
    plt.savefig(__figdir__ + outfile2 + '.' + plotfiletype, **savefig_args)


# %%
# Make a plot for a KML file:
# Do a version of the plot where the axes take the whole figure
fig, ax = plt.subplots(subplot_kw={'projection': ccrs.PlateCarree()})
plt.set_cmap(cmap=plt.get_cmap('turbo'))
cs = ax.pcolormesh(sst.lon, sst.lat, sst, vmin=levels[0], vmax=levels[-1], transform=ccrs.PlateCarree())
add_vel_quiver(tind, ax=ax)
#gdf.plot(ax=ax, color='none', edgecolor='black', linewidth=2, alpha=0.9, transform=ccrs.PlateCarree(), zorder=2)

# remove all whitespace
plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
if savefig:
    outfile2 = 'KML_SST_UV_map_' + t1.replace(' ', '_')
    plt.savefig(__figdir__ + outfile2 + '.' + plotfiletype, **kml_savefig_args)

# %%
functions_Debarshi.create_kml_file(kml_name=__figdir__ + outfile2, overlay_name='SST_UV', plot_file=outfile2 + '.' + plotfiletype, pts_lon=pts_lon, pts_lat=pts_lat, BD=BD, mooring=mooring, IDA=IDA, PLANCK=PLANCK, WHOI43=WHOI43, WHOI1102=WHOI1102,xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax)

# %%
# Calculate the SST difference over the last week
# Get the time range for the last week
t2 = (ds.time[-7].values).astype('datetime64[D]').astype(str)
t1 = (ds.time[-1].values).astype('datetime64[D]').astype(str)
sst_2 = ds.sst.sel(time=t1).sel(lon=slice(xmin, xmax), lat=slice(ymin, ymax))
sst_1 = ds.sst.sel(time=t2).sel(lon=slice(xmin, xmax), lat=slice(ymin, ymax))
sst_diff = sst_2 - sst_1

# Plot the SST difference
levels_diff = np.linspace(-1, 1, 21)  # Adjust levels as needed
fig, ax = plt.subplots(subplot_kw={'projection': ccrs.PlateCarree()})
plt.set_cmap(cmap=plt.get_cmap('RdBu_r'))  # Diverging colormap for differences

cs = ax.pcolormesh(sst_diff.lon, sst_diff.lat, sst_diff, vmin=levels_diff[0], vmax=levels_diff[-1], transform=ccrs.PlateCarree())
cb = plt.colorbar(cs, ax=ax, fraction=0.022, extend='both')
cb.set_label('SST Difference (°C)', fontsize=10)

# Add map features
coast = cartopy.feature.GSHHSFeature(scale="full")
ax.add_feature(coast, zorder=3, facecolor=[.6, .6, .6], edgecolor='black')
ax.add_feature(cartopy.feature.BORDERS, linestyle='-', alpha=0.5, zorder=10)
ax.add_feature(cartopy.feature.RIVERS, edgecolor='blue', alpha=0.25, zorder=10)

# Add gridlines
gl = ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False, alpha=0.5, linestyle='--')
gl.top_labels = False
gl.right_labels = False

# Add titles and labels
ax.set_title(f'SST Difference: {t1} minus {t2}')
ax.set_xlabel('Longitude')
ax.set_ylabel('Latitude')
ax.set_xlim(xmin, xmax)
ax.set_ylim(ymin, ymax)
# add the eez boundaries
#gdf.plot(ax=ax, color='none', edgecolor='black', linewidth=2, alpha=0.9, transform=ccrs.PlateCarree(), zorder=2)
ax.plot(eez[:,0], eez[:,1], 'w-', linewidth=1, transform=ccrs.PlateCarree(), zorder=3,label='EEZ')
#  Add BD/RAMA moorings
bd = ax.plot(pts_lon, pts_lat, 'o', color='m', markeredgecolor='k', markersize=8, transform=ccrs.PlateCarree(), label='BD/RAMA moorings')
for i in range(len(pts_lon)):
    # label the points
    ax.text(pts_lon[i] + 0.1, pts_lat[i] + 0.1, BD[i], fontsize=12, color='m', transform=ccrs.PlateCarree(), zorder=4)

site_2024 = ax.plot(mooring['lon'], mooring['lat'], 'o', color='k', markeredgecolor='w', markersize=8, transform=ccrs.PlateCarree(), label='2024 site')

add_vel_quiver(tind, ax=ax)
# Plot the current waypoint and ship
next_wpt = plt.plot(wpt['lon'], wpt['lat'], 'o', color='r', markeredgecolor='w', markersize=8, transform=ccrs.PlateCarree(), label='Current waypoint')
tgt = plt.plot(longitudes, latitudes, 'o', color='b', markeredgecolor='w', markersize=8, transform=ccrs.PlateCarree(), label='Ship Position')
plt.legend([site_2024[0], bd[0], next_wpt[0], tgt[0]], ['2024 site', 'BD/RAMA moorings', 'Current waypoint', 'Ship Position'], loc='upper right', framealpha=0.8)
ax.plot(eez[:,0], eez[:,1], 'w-', linewidth=1, transform=ccrs.PlateCarree(), zorder=3,label='EEZ')


plt.show()

if savefig:
    outfile2 = 'Delta_SST_UV_map_' + t1.replace(' ', '_')
    plt.savefig(__figdir__ + outfile2 + '.' + plotfiletype, **savefig_args)

# %%
# Now make a plot for a KML file:
# Do a version of the plot where the axes take the whole figure
fig, ax = plt.subplots(subplot_kw={'projection': ccrs.PlateCarree()})
plt.set_cmap(cmap=plt.get_cmap('RdBu_r'))  # Diverging colormap for differences
cs = ax.pcolormesh(sst_diff.lon, sst_diff.lat, sst_diff, vmin=levels_diff[0], vmax=levels_diff[-1], transform=ccrs.PlateCarree())
add_vel_quiver(tind, ax=ax)
#gdf.plot(ax=ax, color='none', edgecolor='black', linewidth=2, alpha=0.9, transform=ccrs.PlateCarree(), zorder=2)

# remove all whitespace
plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
if savefig:
    outfile2 = 'KML_Delta_SST_UV_map_' + t1.replace(' ', '_')
    plt.savefig(__figdir__ + outfile2 + '.' + plotfiletype, **kml_savefig_args)

# %%
functions_Debarshi.create_kml_file(kml_name=__figdir__ + outfile2, overlay_name='Delta_SST_UV', plot_file=outfile2 + '.' + plotfiletype, pts_lon=pts_lon, pts_lat=pts_lat, BD=BD, mooring=mooring, IDA=IDA, PLANCK=PLANCK, WHOI43=WHOI43, WHOI1102=WHOI1102,xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax)


# %%

# Plot the current waypoint and ship
#next_wpt = plt.plot(wpt['lon'], wpt['lat'], 'o', color='r', markeredgecolor='w', markersize=8, transform=ccrs.PlateCarree(), label='Current waypoint')
#tgt = plt.plot(longitudes, latitudes, 'o', color='b', markeredgecolor='w', markersize=8, transform=ccrs.PlateCarree(), label='Ship Position')
#plt.legend([site_2024, bd[0], next_wpt[0], tgt[0]], ['2024 site', 'BD/RAMA moorings', 'Current waypoint', 'Ship Position'], loc='upper right', framealpha=0.8)







# %%
# Export the current waypoint to a KML file; this differs from the other function 
# because it only does the waypoints

# %%
# Create a KML file for the current waypoint
functions_Debarshi.waypoints_to_kml(kml_name=__figdir__ + 'current_waypoint', wpt=wpt)

# %%
# Make a plot of current speed and direction
# Plot the current speed and direction

fig, ax = plt.subplots(subplot_kw={'projection': ccrs.PlateCarree()})
plt.set_cmap(cmap=plt.get_cmap('turbo'))
# Plot the current speed
u = np.squeeze(ds_ssh.ugos.isel(time=tind)) #dtype=object
v = np.squeeze(ds_ssh.vgos.isel(time=tind))
# Calculate the speed
speed = np.sqrt(u**2 + v**2)
# Plot the speed
cs = ax.pcolormesh(ds_ssh.longitude, ds_ssh.latitude, speed, vmin=0, vmax=0.75, transform=ccrs.PlateCarree())
cb = plt.colorbar(cs, ax=ax, fraction=0.022, extend='both')
cb.set_label('Current Speed [m/s]', fontsize=10)
# Add map features
coast = cartopy.feature.GSHHSFeature(scale="full")
ax.add_feature(coast, zorder=3, facecolor=[.6, .6, .6], edgecolor='black')
ax.add_feature(cartopy.feature.BORDERS, linestyle='-', alpha=0.5, zorder=10)
ax.add_feature(cartopy.feature.RIVERS, edgecolor='blue', alpha=0.25, zorder=10)
# Add gridlines
gl = ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False, alpha=0.5, linestyle='--')
gl.top_labels = False
gl.right_labels = False
# Add titles and labels
ax.set_title('Current Speed')
ax.set_xlim(xmin, xmax)
ax.set_ylim(ymin, ymax)
ax.plot(eez[:,0], eez[:,1], 'w-', linewidth=1, transform=ccrs.PlateCarree(), zorder=3,label='EEZ')

add_vel_quiver(tind, ax=ax)
# Add the BD/RAMA moorings
bd = ax.plot(pts_lon, pts_lat, 'o', color='m', markeredgecolor='k', markersize=8, transform=ccrs.PlateCarree(), label='BD/RAMA moorings')
for i in range(len(pts_lon)):
    # label the points
    ax.text(pts_lon[i] + 0.1, pts_lat[i] + 0.1, BD[i], fontsize=12, color='w', transform=ccrs.PlateCarree(), zorder=4)
# Add the 2024 site
site_2024 = ax.plot(mooring['lon'], mooring['lat'], 'o', color='k', markeredgecolor='w', markersize=8, transform=ccrs.PlateCarree(), label='2024 site')
# Add the EEZ boundaries
#gdf.plot(ax=ax, color='none', edgecolor='black', linewidth=2, alpha=0.9, transform=ccrs.PlateCarree(), zorder=2)
# Add the current waypoint and ship
next_wpt = plt.plot(wpt['lon'], wpt['lat'], 'o', color='r', markeredgecolor='w', markersize=8, transform=ccrs.PlateCarree(), label='Current waypoint')
tgt = plt.plot(longitudes, latitudes, 'o', color='b', markeredgecolor='w', markersize=8, transform=ccrs.PlateCarree(), label='Ship Position')
ax.plot(eez[:,0], eez[:,1], 'w-', linewidth=1, transform=ccrs.PlateCarree(), zorder=3,label='EEZ')

plt.legend([site_2024[0], bd[0], next_wpt[0], tgt[0]], ['2024 site', 'BD/RAMA moorings', 'Current waypoint', 'Ship Position'], loc='upper right', framealpha=0.8)
plt.show()
if savefig:
    outfile2 = 'Current_Speed_map_' + t1.replace(' ', '_')
    plt.savefig(__figdir__ + outfile2 + '.' + plotfiletype, **savefig_args)
# %%
# Make a plot for a KML file:
# Do a version of the plot where the axes take the whole figure
fig, ax = plt.subplots(subplot_kw={'projection': ccrs.PlateCarree()})
plt.set_cmap(cmap=plt.get_cmap('turbo'))
# Plot the current speed
cs = ax.pcolormesh(ds_ssh.longitude, ds_ssh.latitude, speed, vmin=0, vmax=0.75, transform=ccrs.PlateCarree())
add_vel_quiver(tind, ax=ax)
# remove all whitespace
plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
if savefig:
    outfile2 = 'KML_Current_Speed_map_' + t1.replace(' ', '_')
    plt.savefig(__figdir__ + outfile2 + '.' + plotfiletype, **kml_savefig_args)
# %%
functions_Debarshi.create_kml_file(kml_name=__figdir__ + outfile2, overlay_name='Current_Speed', plot_file=outfile2 + '.' + plotfiletype, pts_lon=pts_lon, pts_lat=pts_lat, BD=BD, mooring=mooring, IDA=IDA, PLANCK=PLANCK, WHOI43=WHOI43, WHOI1102=WHOI1102, xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax)

# %%
'''
import socket
import simplekml

# UDP server configuration
UDP_IP = "172.26.4.188"  # Listen on all interfaces
UDP_PORT = 55555

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

# Create a KML object
kml = simplekml.Kml()

# Loop to receive data
while True:
    data, addr = sock.recvfrom(1024)
    # Parse the data (replace with your parsing logic)
    latitude = float(data.decode("utf-8").split(",")[0])
    longitude = float(data.decode("utf-8").split(",")[1])
    # Add a Placemark in KML
    pnt = kml.newpoint(name=f"Location {latitude}, {longitude}", coords=[(longitude, latitude)])
    # Save the KML
    kml.save("location_data.kml")
    print(f"Received location: {latitude}, {longitude}")
    time.sleep(1)
'''
# %%
