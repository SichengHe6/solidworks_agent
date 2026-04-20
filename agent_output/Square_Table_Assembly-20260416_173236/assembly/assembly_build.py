# -*- coding: utf-8 -*-
import pythoncom
import win32com.client
import os

class SldWorksAssembly:
    def __init__(self):
        try:
            # 连接 SolidWorks 应用程序
            self.swApp = win32com.client.Dispatch("SldWorks.Application")
            self.swApp.Visible = True
            self.model = None
            print("成功连接到 SolidWorks 应用程序")
        except Exception as e:
            print(f"无法连接到 SolidWorks: {e}")
            raise

    def create_assembly(self, name):
        # 获取默认装配体模板路径
        # swDefaultTemplateAssembly = 8
        template_path = self.swApp.GetUserPreferenceStringValue(8)
        # 新建文档: NewDocument(TemplateName, PaperSize, Width, Height)
        self.model = self.swApp.NewDocument(template_path, 0, 0, 0)
        if self.model:
            # 强制转换为装配体文档接口
            self.assembly_doc = self.model
            print(f"成功创建装配体文档: {name}")
            return True
        return False

    def add_component(self, path, x, y, z):
        """
        使用 AddComponent5 插入零件。
        注意：在某些版本的 win32com 中，需要确保 model 被正确识别为 AssemblyDoc。
        """
        # 检查文件是否存在
        if not os.path.exists(path):
            print(f"错误: 零件文件不存在 {path}")
            return None

        # AddComponent5(Name, Config, Root, IsVirtual, Reserved, X, Y, Z)
        # 注意：SolidWorks API 单位为米 (m)
        comp = self.assembly_doc.AddComponent5(path, 0, "", False, "", x, y, z)
        if comp:
            comp_name = comp.Name2
            print(f"成功插入组件: {comp_name}")
            return comp_name
        else:
            print(f"插入组件失败: {path}")
            return None

    def mate_faces(self, comp1, comp2, face1, face2, aligned=True):
        """平面重合配合"""
        self.model.ClearSelection2(True)
        # 构造选择字符串: "接口名@组件名"
        mark1 = f"{face1}@{comp1}"
        mark2 = f"{face2}@{comp2}"
        
        # 选中两个面
        # SelectByID2(Name, Type, X, Y, Z, Append, Mark, Callout, SelectOption)
        res1 = self.model.Extension.SelectByID2(mark1, "PLANE", 0, 0, 0, True, 1, None, 0)
        res2 = self.model.Extension.SelectByID2(mark2, "PLANE", 0, 0, 0, True, 1, None, 0)
        
        if res1 and res2:
            # AddMate3(Type, Alignment, Flip, Distance, DistanceAbs, GearRatio1, GearRatio2, Angle, AngleAbs, ForPositionOnly, InPlace, ErrorStatus)
            # Type: 1 = swMateCOINCIDENT
            # Alignment: 1 = swMateAlignALIGNED, 2 = swMateAlignOPPOSED
            alignment = 1 if aligned else 2
            mate_res = self.assembly_doc.AddMate3(1, alignment, False, 0, 0, 0, 0, 0, 0, 0, 0, False, 0)
            if mate_res:
                print(f"成功建立平面配合: {mark1} <-> {mark2}")
                return True
        print(f"平面配合失败: {mark1} <-> {mark2}")
        return False

    def mate_axes(self, comp1, comp2, axis1, axis2, aligned=True):
        """同心配合"""
        self.model.ClearSelection2(True)
        mark1 = f"{axis1}@{comp1}"
        mark2 = f"{axis2}@{comp2}"
        
        res1 = self.model.Extension.SelectByID2(mark1, "AXIS", 0, 0, 0, True, 1, None, 0)
        res2 = self.model.Extension.SelectByID2(mark2, "AXIS", 0, 0, 0, True, 1, None, 0)
        
        if res1 and res2:
            # Type: 2 = swMateCONCENTRIC
            alignment = 1 if aligned else 2
            mate_res = self.assembly_doc.AddMate3(2, alignment, False, 0, 0, 0, 0, 0, 0, 0, 0, False, 0)
            if mate_res:
                print(f"成功建立轴线配合: {mark1} <-> {mark2}")
                return True
        print(f"轴线配合失败: {mark1} <-> {mark2}")
        return False

    def save_as(self, path):
        """保存装配体"""
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            # SaveAs3(Name, Options, Errors)
            # Options: 1 = swSaveAsCurrentVersion
            res = self.model.SaveAs3(path, 0, 1)
            return res == 0
        except Exception as e:
            print(f"保存异常: {e}")
            return False

def main():
    # 零件路径定义
    parts_map = {
        "table_top": r"D:\a_src\python\sw_agent\agent_output\Square_Table_Assembly-20260416_173236\parts\table_top\table_top.SLDPRT",
        "table_leg": r"D:\a_src\python\sw_agent\agent_output\Square_Table_Assembly-20260416_173236\parts\table_leg\table_leg.SLDPRT",
        "m8_screw": r"D:\a_src\python\sw_agent\agent_output\Square_Table_Assembly-20260416_173236\parts\m8_screw\m8_screw.SLDPRT"
    }
    assembly_path = r"D:\a_src\python\sw_agent\agent_output\Square_Table_Assembly-20260416_173236\assembly\Square_Table_Assembly.SLDASM"

    builder = SldWorksAssembly()
    if not builder.create_assembly("Square_Table_Assembly"):
        print("创建装配体失败")
        return

    # 1. 插入桌面 (基准件)
    top_comp = builder.add_component(parts_map["table_top"], 0, 0, 0)
    
    # 2. 插入并配合 4 根桌腿
    for i in range(1, 5):
        # 初始位置偏移，防止重叠导致选择错误
        leg_comp = builder.add_component(parts_map["table_leg"], 0.2 * i, 0.2 * i, -0.4)
        if leg_comp:
            # 桌面底面与桌腿顶面贴合 (Opposed)
            builder.mate_faces(top_comp, leg_comp, "bottom_face", "top_end_face", aligned=False)
            # 桌面孔轴线与桌腿孔轴线同心
            builder.mate_axes(top_comp, leg_comp, f"hole_axis_{i}", "leg_hole_axis", aligned=True)
            print(f"桌腿 {i} 装配步骤完成")

    # 3. 插入并配合 4 枚螺钉
    for i in range(1, 5):
        screw_comp = builder.add_component(parts_map["m8_screw"], 0.2 * i, -0.2 * i, 0.2)
        if screw_comp:
            # 螺钉轴线与桌面孔轴线同心
            builder.mate_axes(screw_comp, top_comp, "screw_axis", f"hole_axis_{i}", aligned=True)
            # 螺钉头底面与桌面顶面贴合 (Opposed)
            builder.mate_faces(screw_comp, top_comp, "head_bottom_face", "top_face", aligned=False)
            print(f"螺钉 {i} 装配步骤完成")

    # 4. 保存结果
    if builder.save_as(assembly_path):
        print(f"装配体构建成功: {assembly_path}")
    else:
        print("装配体保存失败")

if __name__ == "__main__":
    main()