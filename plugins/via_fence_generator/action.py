import pcbnew
import os
import math
import wx
from .dialog import Dialog

class ViaFenceAction(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Via Fence Generator"
        self.category = "Modify PCB"
        self.description = "Add via fence to selected tracks"
        self.icon_file_name = os.path.join(os.path.dirname(__file__), "32x32.png")
        self.show_toolbar_button = True

        self.lstDefinedViaSizesOnChoice_is_active = False  # 定義済みサイズが選択されたときの自動テキスト入力により定義済みサイズの選択が解除されてしまうことを避けるためのフラグ
        self.chkUseZoneClearanceOnCheckBox_is_active = False

    # def __init__(self):を使うと怒られが発生する

    def create_via(self, brd, pos, diameter, drill, net_name, is_free, type_, start_layer_id = pcbnew.F_Cu, end_layer_id = pcbnew.B_Cu, remove_unconnected_annular_ring = False):
        via = pcbnew.PCB_VIA(brd)
        via.SetPosition(pcbnew.VECTOR2I(pos[0], pos[1]))
        via.SetWidth(diameter)  # 外径
        via.SetDrill(drill)     # ドリル径
        via.SetNet(brd.FindNet(net_name))  # ネット
        via.SetIsFree(is_free)             # True=手動でビアを置く場合と同じく自動更新されない False=ビアのネットは置かれた場所によって自動更新される
        via.SetViaType(type_)              # pcbnew.VIATYPE_THROUGH,pcbnew.VIATYPE_BLIND_BURIED,pcbnew.VIATYPE_MICROVIA,pcbnew.VIATYPE_NOT_DEFINEDのどれか
        via.SetLayerPair(start_layer_id, end_layer_id)  # レイヤーのID 導体レイヤーは0から31
        via.SetRemoveUnconnected(remove_unconnected_annular_ring)  # True=始点,終点,および接続されたレイヤー False=すべての導体レイヤー
        brd.Add(via)

    def append_position(self, pos_list, pos):  # 座標リストに座標を追加する関数 リストの座標のいずれかと距離がごく近いものは追加されない 円弧と直線の接続部にビアが重なって生成されるのを防ぐが既に基板上にあるビアに対しては無力
        if any(math.dist(pos_stored, pos) < pcbnew.FromMM(0.1) for pos_stored in pos_list):  # 0.1mm以下の距離には複数のビアを配置しない
            return  # すでに登録された座標のどれかと距離が近すぎるので新しく登録せずに終了
        pos_list.append(pos)

    def is_numeric(self, s):  # 文字列が数値を表しているか
        try:
            float(s)
            return True
        except ValueError:
            return False
    '''
    def is_positive_num(self, s):  # 文字列が正の数値を表しているか否か
        try:
            if float(s) > 0:  # 正の数値
                return True
            else:  # 0以下の数値
                return False
        except ValueError:  # そもそも数値ではない
            return False
    '''
    def is_via_size_valid(self, txt_diameter, txt_hole):  # ビアサイズが有効な数値であるか
        try:
            if all([float(txt_diameter) > 0, float(txt_hole) > 0, float(txt_diameter) > float(txt_hole)]):  # ここにアニュラリングの最小幅も含める？
                return True
            else:
                return False
        except ValueError:  # そもそも数値ではない
            return False

    def update_apply_button_state(self):  # Applyボタンを押してもよい諸条件を記述
        self.dlg.subsubSizer3Apply.Enable(all([
            self.dlg.lstStartLayer.GetSelection() != self.dlg.lstEndLayer.GetSelection(),  # レイヤーが同じではない
            self.is_numeric(self.dlg.txtTrackToViaClearance.GetValue()),  # クリアランスが数字である クリアランスは0以下でもよい
            self.is_via_size_valid(self.dlg.txtViaDiameter.GetValue(), self.dlg.txtViaHole.GetValue()),  # ビアサイズが有効な数値であるか
            any(track.IsSelected() for track in self.board.GetTracks())  # いずれかの配線が選択されている
        ]))

    # クリアランス入力補間に関わる割り込み関数
    def chkUseZoneClearanceOnCheckBox(self, event):
        if self.dlg.chkUseZoneClearance.IsChecked():  # Use zone clearanceが有効になったとき,テキストボックスにゾーンのクリアランスを入力
            self.chkUseZoneClearanceOnCheckBox_is_active = True
            self.dlg.txtTrackToViaClearance.SetValue(str(pcbnew.ToMM(self.zone_clearance_list[self.dlg.lstViaNet.GetSelection()])))
            self.chkUseZoneClearanceOnCheckBox_is_active = False

        #self.update_apply_button_state()

    def txtTrackToViaClearanceOnText(self, event):  # 上の関数内のSetValueフラグが立っていないときチェックを外す
        if not self.chkUseZoneClearanceOnCheckBox_is_active:
            self.dlg.chkUseZoneClearance.SetValue(False)

        #self.update_apply_button_state()

    # ビアサイズ入力補間に関わる割り込み関数
    def lstDefinedViaSizesOnChoice(self, event):  # 定義済みビアサイズが選択されたとき,テキストボックスに定義済みサイズを入力
        if self.dlg.lstDefinedViaSizes.GetSelection() != wx.NOT_FOUND:
            self.lstDefinedViaSizesOnChoice_is_active = True
            self.dlg.txtViaDiameter.SetValue(str(pcbnew.ToMM(self.vias_dimensions_list[self.dlg.lstDefinedViaSizes.GetSelection() + 1].m_Diameter)))
            self.dlg.txtViaHole.SetValue(str(pcbnew.ToMM(self.vias_dimensions_list[self.dlg.lstDefinedViaSizes.GetSelection() + 1].m_Drill)))
            self.lstDefinedViaSizesOnChoice_is_active = False

        #self.update_apply_button_state()

    def txtViaSizesOnText(self, event):  # 上の関数内のSetValueフラグが立っていないとき定義済みビアサイズの選択を外す
        if not self.lstDefinedViaSizesOnChoice_is_active:
            self.dlg.lstDefinedViaSizes.SetSelection(wx.NOT_FOUND)

        #self.update_apply_button_state()

    # レイヤーペアの判定と操作の関数(レイヤーペアが隣接していれば当然アニュラリングはAll copper layersに必要になる)
    def check_via_layer_pair_adjacency(self):
        if abs(self.dlg.lstStartLayer.GetSelection() - self.dlg.lstEndLayer.GetSelection()) == 1:  # レイヤーが隣接
            self.dlg.lstAnnularRings.SetSelection(0)  # All copper layersにする
            self.dlg.lstAnnularRings.Enable(False)    # グレーアウトでAll copper layersに固定
        else:
            self.dlg.lstAnnularRings.Enable(True)

    # ビアタイプの判定と操作の関数(ビアタイプがthroughならばレイヤーペアはF.Cu,B.Cuでないといけない)
    def check_via_type_and_set_layer_pair(self):
        if self.dlg.lstViaType.GetSelection() == 0:  # throughが選択されたときレイヤー設定をF.CuとB.Cuにしてからグレーアウト
            self.dlg.lstStartLayer.SetSelection(0)   # F.Cu
            self.dlg.lstEndLayer.SetSelection(self.dlg.lstEndLayer.GetCount() - 1)  # B.Cu
            self.dlg.lstStartLayer.Enable(False)     # グレーアウトでF.Cu,B.Cuに固定
            self.dlg.lstEndLayer.Enable(False)

            self.check_via_layer_pair_adjacency()    # 変更されたレイヤーペアの隣接判定とそれに伴う設定

        else:  # through以外でグレーアウトを解除
            self.dlg.lstStartLayer.Enable(True)
            self.dlg.lstEndLayer.Enable(True)

    def lstViaTypeOnChoice(self, event):  # ビアタイプ変更時に呼ばれる割り込み関数
        self.check_via_type_and_set_layer_pair()

        #self.update_apply_button_state()

    def lstLayerPairOnChoice(self, event):  # レイヤーペア変更時に呼ばれる割り込み関数
        self.check_via_layer_pair_adjacency()  # 変更されたレイヤーペアの隣接判定とそれに伴う設定

        #self.update_apply_button_state()

    def Run(self):  # ツールバーアイコンが押された時に実行
        # ダイアログと基板のオブジェクトを作成
        pcb_frame = next(
            x for x in wx.GetTopLevelWindows() if x.GetName() == "PcbFrame"  # 親ウィンドウの設定
        )
        self.dlg = Dialog(pcb_frame)
        self.board = pcbnew.GetBoard()

        # 配線とビアのクリアランスの補間制御
        self.dlg.chkUseZoneClearance.Bind(wx.EVT_CHECKBOX, self.chkUseZoneClearanceOnCheckBox)  # Use zone clearanceの状態が変化したときに関数を呼び出す

        self.dlg.txtTrackToViaClearance.Bind(wx.EVT_TEXT, self.txtTrackToViaClearanceOnText)

        # すべてのゾーンのネットを登録しクリアランスを取得
        self.zone_clearance_list = []
        for zone in self.board.Zones():  # 登録されないネット無しゾーンにもindexがあるからここにindexつけるのは良くない
            net_name = zone.GetNetname()
            if net_name != None and net_name != "":  # ネット無しゾーンは登録しないしクリアランスの取得もしない
                self.dlg.lstViaNet.Append(net_name)  # ネット名が同じゾーンは重複せずそれぞれ登録される
                if "GND" in net_name:
                    self.dlg.lstViaNet.SetSelection(self.dlg.lstViaNet.GetCount() - 1)  # 現在登録されている数を使うと直近で登録されたものを選べる
                self.zone_clearance_list.append(zone.GetLocalClearance())

        self.dlg.lstViaNet.Bind(wx.EVT_CHOICE, self.chkUseZoneClearanceOnCheckBox)  # ネットが変わったときにクリアランスも更新 チェックが入った時と同じ操作なので関数も同じ
        '''
        # ゾーンのものに限らずすべてのネットを登録する場合
        nets = self.board.GetNetsByName()
        for index, (_ , net) in enumerate(nets.items(), -1):  # ダミーのネット(None?)が存在しているため実際に登録されるのはindex=0番から
            net_name = net.GetNetname()
            if net_name != None and net_name != "":
                self.dlg.lstViaNet.Append(net_name)  # 同名ネットがあっても表示上は一つ
                if "GND" in net_name:
                    self.dlg.lstViaNet.SetSelection(index)
        '''

        # 定義済みビアサイズリストの取得と登録と補間制御
        self.vias_dimensions_list = self.board.GetViasDimensionsList()
        for index, via_dimension in enumerate(self.vias_dimensions_list):  # 0個目(最初)のDiameterとDrillは0になるので登録されない
            if via_dimension.m_Diameter != 0 and via_dimension.m_Drill != 0:
                self.dlg.lstDefinedViaSizes.Append(str(pcbnew.ToMM(via_dimension.m_Diameter)) + " / " + str(pcbnew.ToMM(via_dimension.m_Drill)))
                """
                if ViaDimension.m_Diameter == pcbnew.FromMM(0.6):  # 初期設定
                    self.dlg.lstDefinedViaSizes.SetSelection(index - 1)
                """
        self.dlg.lstDefinedViaSizes.Bind(wx.EVT_CHOICE, self.lstDefinedViaSizesOnChoice)  # 定義済みビアサイズが選択されたときに関数を呼び出す
        self.dlg.txtViaDiameter.Bind(wx.EVT_TEXT, self.txtViaSizesOnText)  # DiameterとHoleどちらのテキストボックスに入力されても呼び出す関数は同じ
        self.dlg.txtViaHole.Bind(wx.EVT_TEXT, self.txtViaSizesOnText)

        # 有効レイヤーの取得と登録(8.0以前)
        '''
        for layer_id in range(32):  # IDが0から31のレイヤーのうち有効なものを登録(初めの32層は全て導体レイヤー)
            if self.board.IsLayerEnabled(layer_id):
                self.dlg.lstStartLayer.Append(self.board.GetLayerName(layer_id))
                self.dlg.lstEndLayer.Append(self.board.GetLayerName(layer_id))
        '''

        # 有効レイヤーの取得と登録(9.0に対応)
        copper_layers = [layer_id for layer_id in range(pcbnew.PCB_LAYER_ID_COUNT) if self.board.IsLayerEnabled(layer_id) and pcbnew.IsCopperLayer(layer_id)]  # 有効な導体レイヤーのIDのリストを取得 pcbnew.PCB_LAYER_ID_COUNTは128になるはず

        inner_layers = [layer_id for layer_id in copper_layers if layer_id not in (pcbnew.F_Cu, pcbnew.B_Cu)]  # 上記リストからF.CuとB.CuのIDを除外

        for layer_id in [pcbnew.F_Cu] + inner_layers + [pcbnew.B_Cu]:
            layer_name = self.board.GetLayerName(layer_id)
            self.dlg.lstStartLayer.Append(layer_name)
            self.dlg.lstEndLayer.Append(layer_name)

        # 内層アニュラリングの選択肢を登録する
        self.dlg.lstAnnularRings.Append("All copper layers")
        self.dlg.lstAnnularRings.Append("Start, end, and connected layers")
        #self.dlg.lstAnnularRings.Append("Connected layers only")  # これの設定方法は不明
        self.dlg.lstAnnularRings.SetSelection(0)  # レイヤーペアが隣接していないときでもAll copper layersを初期設定とするため記述が必要

        # ビアタイプを登録し初期設定をThroughとする
        self.dlg.lstViaType.Append("Through")
        self.dlg.lstViaType.Append("Micro")
        self.dlg.lstViaType.Append("Blind/buried")
        self.dlg.lstViaType.SetSelection(0)
        self.dlg.lstViaType.Bind(wx.EVT_CHOICE, self.lstViaTypeOnChoice)  # ビアタイプが選択されたときに関数を呼び出す

        # ビアタイプの初期設定がthroughならばF.CuとB.Cuをレイヤーペアの初期設定としてグレーアウトしさらにそれらの隣接判定を行う
        self.check_via_type_and_set_layer_pair()  # through以外ならばレイヤーペアは設定されないし隣接判定も行われない

        self.dlg.lstStartLayer.Bind(wx.EVT_CHOICE, self.lstLayerPairOnChoice)  # レイヤーペア変更時に隣接判定を行う
        self.dlg.lstEndLayer.Bind(wx.EVT_CHOICE, self.lstLayerPairOnChoice)

        #self.update_apply_button_state()

        self.dlg.subsubSizer3Apply.Bind(wx.EVT_BUTTON, self.subsubSizer3OnApplyButtonClick)
        self.dlg.subsubSizer3Cancel.Bind(wx.EVT_BUTTON, self.subsubSizer3OnCancelButtonClick)

        self.dlg.Show()

        self.timer = wx.Timer(self.dlg)
        self.dlg.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
        self.timer.Start(100)  # 100ms

    def OnTimer(self, event):
        self.update_apply_button_state()

    def subsubSizer3OnCancelButtonClick(self, event):
        self.timer.Stop()
        self.dlg.Destroy()

    def subsubSizer3OnApplyButtonClick(self, event):
        # netの読み込み 選択していないとネット無しになるがエラーは無い
        via_net_name = self.dlg.lstViaNet.GetStringSelection()

        # ビアのネットの自動更新の有無 自動更新無しがTrue
        via_is_free = not self.dlg.chkUpdateViaNet.IsChecked()

        # ビアタイプ読み込み 何かしらが必ず選択されている
        VIA_TYPE_LIST = [pcbnew.VIATYPE_THROUGH,pcbnew.VIATYPE_MICROVIA, pcbnew.VIATYPE_BLIND_BURIED,pcbnew.VIATYPE_NOT_DEFINED]
        via_type = VIA_TYPE_LIST[self.dlg.lstViaType.GetSelection()]

        # 配線とビアのクリアランスの読み込み
        if self.dlg.chkUseZoneClearance.IsChecked():
            # Use zone clearanceにチェック時は導体ゾーンのクリアランスを使用
            track_to_via_clearance = self.zone_clearance_list[self.dlg.lstViaNet.GetSelection()]
        else:
            # 無効時はテキストボックスから テキストボックスを編集するとチェックが外れる
            track_to_via_clearance = pcbnew.FromMM(float(self.dlg.txtTrackToViaClearance.GetValue()))

        # ビアサイズの読み込み
        if self.dlg.lstDefinedViaSizes.GetSelection() != wx.NOT_FOUND:
            # 定義済みサイズが選択されているときはリストから 割り込みにより定義済みサイズが選択されると同時にテキストボックスにも同じサイズが書き込まれる
            via_diameter = self.vias_dimensions_list[self.dlg.lstDefinedViaSizes.GetSelection() + 1].m_Diameter  # テキストにも書き込まれているが変換されてるので元の値を使う
            via_drill    = self.vias_dimensions_list[self.dlg.lstDefinedViaSizes.GetSelection() + 1].m_Drill
        else:
            # 選択されていないときはテキストボックスから テキストボックスを編集すると選択が解除されてwx.NOT_FOUNDになる
            via_diameter = pcbnew.FromMM(float(self.dlg.txtViaDiameter.GetValue()))
            via_drill    = pcbnew.FromMM(float(self.dlg.txtViaHole.GetValue()))

        # レイヤーペアの読み込み 何かしらが必ず選択されている
        via_start_layer_id = self.board.GetLayerID(self.dlg.lstStartLayer.GetStringSelection())  # layer_idを保持するのは大変なのでレイヤー名だけ保持してここでIDに変換
        via_end_layer_id   = self.board.GetLayerID(self.dlg.lstEndLayer.GetStringSelection())    # StartとEndのレイヤーの上下が逆の場合はKiCadが戻してくれる

        # 内層アニュラリングの除去の有無
        via_remove_unconnected_annular_ring = bool(self.dlg.lstAnnularRings.GetSelection())  # 0=All copper layers=False, 1=True

        # 選択中の配線の取得とビアの配置
        via_position_list = []  # ダイアログを閉じないと一度配置した位置に再度置けないのは困るのでこれはApplyを押すたびに定義
        selected_tracks = [t for t in self.board.GetTracks() if t.IsSelected()]
        for track in selected_tracks:
            track.ClearSelected()  # 選択状態を解除

            track_start = track.GetStart()
            track_end = track.GetEnd()
            track_width = track.GetWidth()
            track_length = track.GetLength()

            offset = track_width//2 + via_diameter//2 + track_to_via_clearance  # python3においては//で切り捨て除算

            if track.GetClass() == "PCB_TRACK":
                DX = track_end.x - track_start.x  # 整数
                DY = track_end.y - track_start.y
                sin_ratio = -DY / track_length  # 0to1
                cos_ratio =  DX / track_length
                dx = int(offset * sin_ratio)  # 整数
                dy = int(offset * cos_ratio)

                via_num = 1 + int(track_length / via_diameter)  # 何故か//を使うとViaNumがfloatになり動作せず

                for step in range(via_num):
                    if via_num == 1:  # stepが0の場合のみ
                        x_temp = track_start.x  # ビアを1個しか置けなくても置く 1個だけ置かれてるのは見れば分かるのでエラーは出さない
                        y_temp = track_start.y
                    else:  # 配線が短くてViaが1個しか置けないとゼロ除算になるのを回避する
                        x_temp = track_start.x + step * int(DX / (via_num - 1))  # +=を使う方法より分かりやすい
                        y_temp = track_start.y + step * int(DY / (via_num - 1))

                    self.append_position(via_position_list, [x_temp - dx, y_temp - dy])
                    self.append_position(via_position_list, [x_temp + dx, y_temp + dy])

            elif track.GetClass() == "PCB_ARC":
                track_center = track.GetCenter()  # 回転中心
                track_radius = track.GetRadius()  # 半径

                inner_radius = track_radius - offset
                outer_radius = track_radius + offset
                angle_disp     = track.GetAngle().AsRadians()
                angle_start = track.GetArcAngleStart().AsRadians()

                if offset > track_radius:  # 円弧半径が小さすぎて内側にビアを置くとクリアランスが保てない場合
                    inner_via_num = 0  # 内側にビアを置かない
                elif via_diameter**2 > 4*inner_radius**2:  # acosが範囲外エラーになる条件
                    inner_via_num = 1
                else:
                    inner_via_num = 1 + int(abs(angle_disp)/math.acos(1 - via_diameter**2/(2*inner_radius**2)))  # 何故か//を使うとViaNumがfloatになり動作せず

                outer_via_num = 1 + int(abs(angle_disp)/math.acos(1 - via_diameter**2/(2*outer_radius**2)))  # ここのangle_dは絶対値でないといけない

                # 内側に置けない場合でも外側に置けるなら置く
                for step in range(inner_via_num):
                    if inner_via_num == 1:
                        angle_temp = angle_start
                    else:
                        angle_temp = angle_start + step * angle_disp / (inner_via_num - 1)  # ここのangle_dは正負問わない

                    self.append_position(via_position_list, [track_center.x + int(inner_radius*math.cos(angle_temp)), track_center.y + int(inner_radius*math.sin(angle_temp))])
                for step in range(outer_via_num):
                    if outer_via_num == 1:
                        angle_temp = angle_start
                    else:
                        angle_temp = angle_start + step * angle_disp / (outer_via_num - 1)

                    self.append_position(via_position_list, [track_center.x + int(outer_radius*math.cos(angle_temp)), track_center.y + int(outer_radius*math.sin(angle_temp))])

        for via_position in via_position_list:  # リストにある座標にビアを配置
            self.create_via(self.board, via_position, via_diameter, via_drill, via_net_name, via_is_free, via_type, via_start_layer_id, via_end_layer_id, via_remove_unconnected_annular_ring)
        pcbnew.Refresh()
