bl_info = {
    "name": "Distribute Grease Pencil Strokes",
    "author": "John Nyquist BFCT",
    "version": (1, 0, 1),
    "blender": (4, 4, 0),
    "location": "View3D > Sidebar > Distribute Strokes",
    "description": "Evenly distribute selected Grease Pencil strokes along X, Y, or Z",
    "category": "Grease Pencil",
}

import bpy
from bpy.props import EnumProperty

# Helper function to get selected strokes and their count
def get_selected_strokes(context):
    obj = context.object
    if obj and obj.type == 'GREASEPENCIL':
        layer = obj.data.layers.active
        if layer and layer.frames:
            current_frame = context.scene.frame_current
            frame = next((f for f in layer.frames if f.frame_number == current_frame), None)
            if frame and frame.drawing.strokes:
                strokes = frame.drawing.strokes
                selected_strokes = [
                    (stroke, sum(getattr(p.position, context.window_manager.gp_distribute_axis.lower()) for p in stroke.points) / len(stroke.points))
                    for stroke in strokes if stroke.select and len(stroke.points) > 0
                ]
                selected_count = len(selected_strokes)
                return selected_count, selected_strokes, strokes
    return 0, [], None

# Operator to run the distribution
class GPENCIL_OT_DistributeStrokes(bpy.types.Operator):
    bl_idname = "gpencil.distribute_strokes"
    bl_label = "Distribute Selected Strokes"
    bl_description = "Evenly distribute selected Grease Pencil strokes along the chosen axis (X, Y, or Z)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        selected_count, _, _ = get_selected_strokes(context)
        return selected_count >= 3

    def execute(self, context):
        axis = context.window_manager.gp_distribute_axis
        selected_count, selected_strokes, _ = get_selected_strokes(context)

        selected_strokes.sort(key=lambda x: x[1])
        strokes_sorted = [s[0] for s in selected_strokes]
        centers = [s[1] for s in selected_strokes]

        low, high = centers[0], centers[-1]
        n = len(strokes_sorted)

        for i in range(1, n - 1):
            target = low + (high - low) * i / (n - 1)
            offset = target - centers[i]
            for point in strokes_sorted[i].points:
                val = getattr(point.position, axis.lower())
                setattr(point.position, axis.lower(), val + offset)

        self.report({'INFO'}, f"Distributed {n - 2} strokes along {axis}-axis.")
        return {'FINISHED'}

# UI Panel
class GPENCIL_PT_DistributePanel(bpy.types.Panel):
    bl_label = "Distribute Strokes"
    bl_idname = "GPENCIL_PT_distribute_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Distribute Strokes'

    def draw(self, context):
        layout = self.layout

        # Get selected stroke count
        selected_count, _, _ = get_selected_strokes(context)

        # Display appropriate message based on selected stroke count
        if selected_count < 3:
            layout.label(text=f"Select 3 or more strokes, {selected_count} selected")
        else:
            layout.label(text=f"Strokes Selected: {selected_count}")

        layout.prop(context.window_manager, "gp_distribute_axis", expand=True)
        layout.operator("gpencil.distribute_strokes")

# Register axis property in the WindowManager
def register():
    bpy.utils.register_class(GPENCIL_OT_DistributeStrokes)
    bpy.utils.register_class(GPENCIL_PT_DistributePanel)

    bpy.types.WindowManager.gp_distribute_axis = EnumProperty(
        name="Axis",
        description="Axis to distribute strokes along",
        items=[
            ('X', "X", "Distribute along X-axis"),
            ('Y', "Y", "Distribute along Y-axis"),
            ('Z', "Z", "Distribute along Z-axis"),
        ],
        default='Z'
    )

def unregister():
    bpy.utils.unregister_class(GPENCIL_OT_DistributeStrokes)
    bpy.utils.unregister_class(GPENCIL_PT_DistributePanel)
    del bpy.types.WindowManager.gp_distribute_axis

if __name__ == "__main__":
    register()