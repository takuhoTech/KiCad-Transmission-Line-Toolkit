import pcbnew
import os

class PadToOriginAction(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Grid Origin Aligner"
        self.category = "Design PCB"
        self.description = "Align the grid origin to the selected pad position"
        self.icon_file_name = os.path.join(os.path.dirname(__file__), "32x32.png")
        self.show_toolbar_button = True

    def Run(self):
        # ボードとデザイン設定を取得
        board = pcbnew.GetBoard()
        design = board.GetDesignSettings()

        # パッドの座標を取得
        pads = [pad for pad in board.GetPads() if pad.IsSelected()]
        if not pads:
            return  # パッドが選択されていない
        pos = pads[0].GetPosition()

        # グリッド原点
        design.SetGridOrigin(pos)
        # ドリル原点はSetAuxOriginで設定

        pcbnew.Refresh()