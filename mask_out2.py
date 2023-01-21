# -*- coding: UTF-8 -*-

from collections.abc import Iterable

import cartopy.crs as ccrs
import matplotlib as mpl
import shapefile
import shapely


class get_maskout:

    def get_shp_area_str(self, shp_path):
        area_str = []
        shp_file = shapefile.Reader(shp_path, encoding="gb18030")
        for k in range(len(shp_file.records()[0])):
            for shape_rec in shp_file.shapeRecords():
                if isinstance(shape_rec.record[k], bytes):
                    area_str.append(str(shape_rec.record[k].decode("gbk")))
                else:
                    area_str.append(str(shape_rec.record[k]))
        
        return area_str

    def find_region(self, shp_path, area_str):

        shp_file = shapefile.Reader(shp_path, encoding="gb18030")
        opt = 0
        for k in range(len(shp_file.records()[0])):
            i = 0
            for shape_rec in shp_file.shapeRecords():
                if isinstance(shape_rec.record[k], bytes):
                    if str(shape_rec.record[k].decode("gbk")) == area_str:
                        return k, i, shape_rec.record[k]
                else:
                    if str(shape_rec.record[k]) == area_str:
                        return k, i, shape_rec.record[k]
                i = i + 1
        if opt == 0:
            print("无此区域")

    def maskout_points(self, lon, lat, shp_path, area_str):

        if area_str == ["THE_ALL"]:
            point_locs = get_maskout_all().maskout_points(lon, lat, shp_path)
            return point_locs

        point_locs = []
        for i in range(len(area_str)):
            region_k, region_i, region_str = self.find_region(shp_path, area_str[i])
            p = mpl.path.Path(shapefile.Reader(shp_path, encoding="gbk").shapes()[region_i].points)
            for j in range(len(lon)):
                if p.contains_points([[lon[j], lat[j]]]):
                    point_locs = point_locs + [j]

        return point_locs

    def in_areas_points(self, cn, shp_path, area_str, proj=ccrs.PlateCarree()):

        cn_points = self.get_contour_verts(cn)
        clabels_manual = []

        for item in cn_points:

            lon = [i[0] for i in item["coords"]]
            lat = [i[1] for i in item["coords"]]

            point_locs = self.maskout_points(lon, lat, shp_path, area_str)

            get_dd = tuple([(proj.transform_point(lon[i], lat[i], ccrs.Geodetic())) for i in point_locs])
            if int(len(get_dd)/2) != 0:
                clabels_manual.append(get_dd[int(len(get_dd)/2)])

        get_clabels_manual = tuple(clabels_manual)

        return get_clabels_manual

    def get_contour_verts(self, cn):
        contours = []
        idx = 0
        for cc, vl in zip(cn.collections, cn.levels):
            for pp in cc.get_paths():
                paths = {}
                paths["id"] = idx
                paths["type"] = 0
                paths["value"] = float(vl)
                xy = []
                for vv in pp.iter_segments():
                    xy.append([float(vv[0][0]), float(vv[0][1])])
                paths["coords"] = xy
                contours.append(paths)
                idx += 1

        return contours

    def maskout_areas(self, originfig, ax, shp_path, area_str, proj=None, clabel=None, vcplot=False):

        if area_str == ["THE_ALL"]:
            get_maskout_all().maskout_areas(originfig, ax, shp_path, proj, clabel, vcplot)
            return 0

        region = []
        for i in range(len(area_str)):
            region_k, region_i, region_str = self.find_region(shp_path, area_str[i])
            region.append(region_str)

        sf = shapefile.Reader(shp_path, encoding="gb18030")
        vertices = []
        codes = []
        for shape_rec in sf.shapeRecords():
            if shape_rec.record[int(region_k)] in region:
                pts = shape_rec.shape.points
                prt = list(shape_rec.shape.parts) + [len(pts)]
                for i in range(len(prt) - 1):
                    for j in range(prt[i], prt[i + 1]):
                        if proj:
                            vertices.append(proj.transform_point(pts[j][0], pts[j][1], ccrs.Geodetic()))
                        else:
                            vertices.append((pts[j][0], pts[j][1]))
                    codes += [mpl.path.Path.MOVETO]
                    codes += [mpl.path.Path.LINETO] * (prt[i + 1] - prt[i] - 2)
                    codes += [mpl.path.Path.CLOSEPOLY]
                clip = mpl.path.Path(vertices, codes)
                clip = mpl.patches.PathPatch(clip, transform=ax.transData)

        if vcplot:
            if isinstance(originfig, Iterable):
                for ivec in originfig:
                    ivec.set_clip_path(clip)
            else:
                originfig.set_clip_path(clip)
        else:
            for contour in originfig.collections:
                contour.set_clip_path(clip)

        if clabel:
            clip_map_shapely = shapely.geometry.Polygon(vertices)
            for text_object in clabel:
                if not clip_map_shapely.contains(shapely.geometry.Point(text_object.get_position())):
                    text_object.set_visible(False)
