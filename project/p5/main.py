# project: p5
# submitter: zdai38
# partner: none

import click
from zipfile import ZipFile,ZIP_DEFLATED
import csv
from io import TextIOWrapper
import socket, struct
import re
import geopandas
import matplotlib.pyplot as plt
from collections import defaultdict
import json
import mapclassify
from matplotlib.animation import FuncAnimation

def zip_csv_iter(name):
    with ZipFile(name) as zf:
        with zf.open(name.replace(".zip", ".csv")) as f:
            reader = csv.reader(TextIOWrapper(f))
            for row in reader:
                yield row
                
def ip2long(ip):
    """
    Convert an IP string to long
    """
    ip = re.sub(r"[a-z]", "0", ip) # substitute zeros for the anonymizing digits
    packedIP = socket.inet_aton(ip)
    return struct.unpack("!L", packedIP)[0]

@click.command()
@click.argument('zip1')
@click.argument('zip2')
@click.argument('mod', type=click.INT)
def sample(zip1, zip2, mod):
    print("zip1:", zip1)
    print("zip2:", zip2)
    print("mod:", mod)
    
    reader = zip_csv_iter(zip1)
    header = next(reader)
    # ip_idx = header.index("ip")
    
    num = 0
    with ZipFile(zip2, "w", compression=ZIP_DEFLATED) as zf:
        with zf.open(zip2.replace(".zip", ".csv"),"w") as f:
            with TextIOWrapper(f) as text:
                w = csv.writer(text)
                w.writerow(header) 
                for i in reader:
                    if num % mod ==0:
                        w.writerow(i)
                    num += 1

    
@click.command()
@click.argument('zip1')
@click.argument('zip2')
def country(zip1,zip2):
    reader = zip_csv_iter(zip1)
    header = next(reader)
    header.append("country")
    
    rows = list(reader)
    rows.sort(key = lambda x:ip2long(x[0])) # sort rows with converted IP
    
    with ZipFile("IP2LOCATION-LITE-DB1.CSV.ZIP") as zf:
        with zf.open("IP2LOCATION-LITE-DB1.CSV.ZIP"[:-4]) as f:
            csv_read = csv.reader(TextIOWrapper(f))
            country = list(csv_read)
                
    # TODO: write the new zip file    
    with ZipFile(zip2, "w") as z:
        with z.open(zip2.replace(".zip", ".csv"),"w") as c:
            with TextIOWrapper(c) as text:
                w = csv.writer(text)
                w.writerow(header)
                idx = 0
                for row in rows:
                    ip_num = ip2long(row[0])

                    result = False
                    while result == False:
                        if ip_num >= int(country[idx][0]) and ip_num <= int(country[idx][1]):
                            result = True
                            row.append(country[idx][3])
                            w.writerow(row)
                        else:
                            idx += 1

    
def world(conti = None):
    world = geopandas.read_file(geopandas.datasets.get_path('naturalearth_lowres'))
    world = world[world["continent"] != "Antarctica"]
    return world

@click.command()
@click.argument('zipname')
@click.argument('svgfile')
@click.argument('hour', type=click.INT)
def geohour(zipname, svgfile, hour):
    # count occurences per country
    reader = zip_csv_iter(zipname)
    header = next(reader)
    cidx = header.index("country")
    timeidx = header.index("time")
    counts = defaultdict(int)
    w = world()
    w["count"] = int()

    # populate counts 
    for row in reader:
        if hour != None:
            if hour != int(row[timeidx].split(":")[0]):
                continue # ???
        counts[row[cidx]] += 1
    
    dct = {}
    for country, count in counts.items():
        # print(country, count)
        # sometimes country names in IP dataset don't match names in naturalearth_lowres -- skip those
        if not country in w["name"].values:
            continue
        # add data (either count or a color) to a new column
        else:
            idx = w[w["name"] == country].index[0]
            # print(idx)
            w.iloc[idx,-1] = count
            dct[country] = count
    # print(dct)
    ax = w.plot(column="count", cmap="Purples", figsize=(16,16), scheme='maximum_breaks', legend = True)
    # plt.legend(loc="upper left", frameon=False)
    fig = ax.get_figure()
    fig.savefig(svgfile, bbox_inches="tight")
    
    # output json file
    lst = sorted(dct.items(), key=lambda x: x[1])
    lst = lst[-5:]
    with open("top_5_h{}.json".format(hour),"w") as f:
        json.dump(dict(lst), f) 

@click.command()
@click.argument('zipfile')
@click.argument('svgfile')
@click.argument('conti', type=click.STRING)
def geocontinent(zipfile, svgfile, conti):
    reader = zip_csv_iter(zipfile)
    header = next(reader)
    cidx = header.index("country")
    counts = defaultdict(int)
    w = world()
    w["count"] = int()

    # populate counts 
    for row in reader:
        counts[row[cidx]] += 1
    
    for country, count in counts.items():
        print(country, count)
        # sometimes country names in IP dataset don't match names in naturalearth_lowres -- skip those
        if not country in w["name"].values:
            continue
            
        # add data (either count or a color) to a new column
        elif (w.loc[w['name'] == country, "continent"] == conti).values[0]:
            w.loc[w['name'] == country, "count"] = count
    
    ax = w.plot(column="count", cmap="Purples", figsize=(16,16), scheme='natural_breaks', legend = True)
    # plt.legend(loc="upper left", frameon=False)
    fig = ax.get_figure()
    fig.savefig(svgfile, bbox_inches="tight")

    
    
def helper(zipname, ax = None, hour = None):
    # count occurences per country
    reader = zip_csv_iter(zipname)
    header = next(reader)
    cidx = header.index("country")
    timeidx = header.index("time")
    counts = defaultdict(int)
    w = world()
    w["count"] = 0

    # populate counts 
    for row in reader:
        if hour != None:
            if hour != int(row[timeidx].split(":")[0]):
                continue 
        counts[row[cidx]] += 1
    
    for country, count in counts.items():
        print(country, count)
        # sometimes country names in IP dataset don't match names in naturalearth_lowres -- skip those
        if not country in w["name"].values:
            continue
        # add data (either count or a color) to a new column
        else:
            idx = w[w["name"] == country].index[0]
            # print(idx)
            w.iloc[idx,-1] = count
    
    w.plot(column="count", cmap="Purples", figsize=(16,16), scheme='maximum_breaks', legend = True, ax= ax)
    # plt.legend(loc="upper left", frameon=False)
    fig = ax.get_figure()
    return fig

    
@click.command()
@click.argument('zipfile')
@click.argument('html_file')
def video(zipfile, html_file):
    fig, ax = plt.subplots()
    
    def call_helper(frames):
        helper(zipfile, ax, frames)
        
    anim = FuncAnimation(fig, call_helper, frames = 23, interval = 250)    
    html = anim.to_html5_video()
    plt.close()
    
    # html output
    with open(html_file, "w") as f:
        f.write(html)
    f.close()



@click.group()
def commands():
    pass

commands.add_command(sample)
commands.add_command(country)
commands.add_command(geohour)
commands.add_command(geocontinent)
commands.add_command(video)
if __name__ == "__main__":
    commands()
    