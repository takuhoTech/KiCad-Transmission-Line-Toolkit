import pcbnew
import os
import math
import numpy as np


class SquareTrackAction(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Square Track Generator"
        self.category = "Modify PCB"
        self.description = "Change selected tracks to square-ended"
        self.icon_file_name = os.path.join(os.path.dirname(__file__), "32x32.png")
        self.show_toolbar_button = True

    def Run(self):
        board = pcbnew.GetBoard()
        selected_tracks = [t for t in board.GetTracks() if t.IsSelected()]

        for track in selected_tracks:
            start = track.GetStart()
            end = track.GetEnd()
            width = track.GetWidth()
            length = track.GetLength()
            layer = track.GetLayer()  # レイヤーIDを取得 別解:layer = board.GetLayerID(track.GetLayerName())
            net = track.GetNet()      # ネットを取得
            board.Remove(track)       # 元の配線を削除

            chain = pcbnew.SHAPE_LINE_CHAIN()  # ポリゴン座標

            if track.GetClass() == 'PCB_TRACK':
                sin_ratio = -(end.y - start.y) / length
                cos_ratio = (end.x - start.x) / length
                dx = round((width / 2) * sin_ratio)
                dy = round((width / 2) * cos_ratio)

                chain.Append(start.x - dx, start.y - dy)
                chain.Append(start.x + dx, start.y + dy)
                chain.Append(end.x + dx, end.y + dy)
                chain.Append(end.x - dx, end.y - dy)

            elif track.GetClass() == 'PCB_ARC':
                center = track.GetCenter()  # 回転中心
                radius = track.GetRadius()  # 半径
                angle_disp = round(track.GetAngle().AsDegrees() * 10)
                angle_start = round(track.GetArcAngleStart().AsDegrees() * 10)

                # 1度ずつ点を打つ処理にすると開始点と終点の角度が整数でないとき精度を保つ処理が面倒なので1/10度ずつ打つ
                for t in range(angle_start, angle_start + angle_disp + np.sign(angle_disp), np.sign(angle_disp)):
                    chain.Append(
                        center.x + round((radius - width / 2) * math.cos(math.radians(t / 10))),
                        center.y + round((radius - width / 2) * math.sin(math.radians(t / 10))),
                    )

                for t in range(angle_start + angle_disp, angle_start - np.sign(angle_disp), -np.sign(angle_disp)):
                    chain.Append(
                        center.x + round((radius + width / 2) * math.cos(math.radians(t / 10))),
                        center.y + round((radius + width / 2) * math.sin(math.radians(t / 10))),
                    )
                # Python3環境ではint/int=float

            chain.SetClosed(True)
            poly_set = pcbnew.SHAPE_POLY_SET()
            poly_set.AddOutline(chain)

            poly = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_POLY)
            poly.SetPolyShape(poly_set)
            poly.SetWidth(0)
            poly.SetFilled(True)
            poly.SetLayer(layer)
            poly.SetNet(net)
            board.Add(poly)

        pcbnew.Refresh()
