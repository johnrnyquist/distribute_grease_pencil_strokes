bl_info = {
    "name": "Distribute Grease Pencil Strokes",
    "author": "John Nyquist BFCT",
    "version": (1, 0, 2),
    "blender": (4, 4, 0),
    "location": "View3D > Sidebar > Distribute Strokes",
    "description": "Evenly distribute selected Grease Pencil strokes along X, Y, or Z",
    "category": "Grease Pencil",
}

import bpy
from bpy.props import EnumProperty

# Helper function to get selected strokes from all layers
def get_selected_strokes(context):
    obj = context.object
    if obj and obj.type == 'GREASEPENCIL':
        selected_strokes = []
        axis_lower = context.window_manager.gp_distribute_axis.lower()
        for layer in obj.data.layers:
            # Find the frame at the current frame number for this layer
            frame = next((f for f in layer.frames if f.frame_number == context.scene.frame_current), None)
            if frame and frame.drawing.strokes:
                for stroke in frame.drawing.strokes:
                    if stroke.select and len(stroke.points) > 0:
                        # Calculate average position along the chosen axis
                        average_pos = sum(getattr(p.position, axis_lower) for p in stroke.points) / len(stroke.points)
                        selected_strokes.append((stroke, average_pos))
        selected_count = len(selected_strokes)
        return selected_count, selected_strokes, None  # Third value kept for consistency, though unused
    return 0, [], None

# Operator to distribute strokes
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

        # Sort strokes by their average position along the axis
        selected_strokes.sort(key=lambda x: x[1])
        strokes_sorted = [s[0] for s in selected_strokes]
        centers = [s[1] for s in selected_strokes]

        # Distribute strokes between the first and last positions
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

# UI Panel with enhanced feedback
class GPENCIL_PT_DistributePanel(bpy.types.Panel):
    bl_label = "Distribute Strokes"
    bl_idname = "GPENCIL_PT_distribute_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Distribute Strokes'

    def draw(self, context):
        layout = self.layout
        obj = context.object

        # Provide detailed feedback based on context
        if not obj or obj.type != 'GREASEPENCIL':
            layout.label(text="Select a Grease Pencil object")
            return
        if not obj.data.layers:
            layout.label(text="No layers in Grease Pencil object")
            return
        has_frame = any(
            any(f.frame_number == context.scene.frame_current for f in layer.frames)
            for layer in obj.data.layers
        )
        if not has_frame:
            layout.label(text="No frames at current frame number in any layer")
            return

        selected_count, _, _ = get_selected_strokes(context)
        if selected_count < 3:
            layout.label(text=f"Select at least 3 strokes ({selected_count} selected)")
        else:
            layout.label(text=f"Strokes Selected: {selected_count}")

        # Show axis selector and operator button
        layout.prop(context.window_manager, "gp_distribute_axis", expand=True)
        layout.operator("gpencil.distribute_strokes")

# Register the addon
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