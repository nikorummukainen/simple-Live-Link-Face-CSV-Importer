import bpy
import csv

from bpy.app.handlers import persistent
from pathlib import Path
from mathutils import Euler

bl_info = {
    "name": "Simple Live Link Face animator",
	"version" : (0, 9, 2),
    "blender": (4, 5, 0),
	"location" : "View3D",
    "category": "Animation",
}



class CSV_Data_Frames(bpy.types.PropertyGroup):
	value : bpy.props.FloatProperty()
bpy.utils.register_class(CSV_Data_Frames)

class CSV_Data_Keys(bpy.types.PropertyGroup):
	name : bpy.props.StringProperty()
	frames : bpy.props.CollectionProperty(type=CSV_Data_Frames)
	frames_index : bpy.props.IntProperty()
bpy.utils.register_class(CSV_Data_Keys)

class CSV_Data(bpy.types.PropertyGroup):
	sources : bpy.props.CollectionProperty(type=CSV_Data_Keys)
	sources_index : bpy.props.IntProperty()

class ARKIT_Key_Block(bpy.types.PropertyGroup):
	name : bpy.props.StringProperty()
bpy.utils.register_class(ARKIT_Key_Block)

class ARKIT_Shape_Keys(bpy.types.PropertyGroup):
	name : bpy.props.StringProperty()
	key_blocks : bpy.props.CollectionProperty(type=ARKIT_Key_Block)
bpy.utils.register_class(ARKIT_Shape_Keys)

class ARKIT_Data(bpy.types.PropertyGroup):
	shape_keys :  bpy.props.CollectionProperty(type=ARKIT_Shape_Keys)

''' Properties '''
csv_filepath = bpy.props.StringProperty(subtype='FILE_PATH')
matched_keys = bpy.props.IntProperty(default = 0, subtype='UNSIGNED')
csv_frames = bpy.props.IntProperty(default = 0, subtype='UNSIGNED')
csv_sources = bpy.props.IntProperty(default = 0, subtype='UNSIGNED')
armature = bpy.props.PointerProperty(type=bpy.types.Object)
head_bone = bpy.props.StringProperty()
left_eye = bpy.props.StringProperty()
right_eye = bpy.props.StringProperty()
csv_data_dict = dict()
matched_shapekeys_dict = dict()
arkit_shapekeys = (
	"eyeBlinkLeft",
	"eyeLookDownLeft",
	"eyeLookInLeft",
	"eyeLookOutLeft",
	"eyeLookUpLeft",
	"eyeSquintLeft",
	"eyeWideLeft",
	"eyeBlinkRight",
	"eyeLookDownRight",
	"eyeLookInRight",
	"eyeLookOutRight",
	"eyeLookUpRight",
	"eyeSquintRight",
	"eyeWideRight",
	"jawForward",
	"jawRight",
	"jawLeft",
	"jawOpen",
	"mouthClose",
	"mouthFunnel",
	"mouthPucker",
	"mouthRight",
	"mouthLeft",
	"mouthSmileLeft",
	"mouthSmileRight",
	"mouthFrownLeft",
	"mouthFrownRight",
	"mouthDimpleLeft",
	"mouthDimpleRight",
	"mouthStretchLeft",
	"mouthStretchRight",
	"mouthRollLower",
	"mouthRollUpper",
	"mouthShrugLower",
	"mouthShrugUpper",
	"mouthPressLeft",
	"mouthPressRight",
	"mouthLowerDownLeft",
	"mouthLowerDownRight",
	"mouthUpperUpLeft",
	"mouthUpperUpRight",
	"browDownLeft",
	"browDownRight",
	"browInnerUp",
	"browOuterUpLeft",
	"browOuterUpRight",
	"cheekPuff",
	"cheekSquintLeft",
	"cheekSquintRight",
	"noseSneerLeft",
	"noseSneerRight",
	"tongueOut",
	"headYaw",
	"headPitch",
	"headRoll",
	"leftEyeYaw",
	"leftEyePitch",
	"leftEyeRoll",
	"rightEyeYaw",
	"rightEyePitch",
	"rightEyeRoll"
)

@persistent
def llf_load_post_handler(dummy):
	bpy.context.scene.llf_frames = 0
	bpy.context.scene.llf_sources = 0
	bpy.context.scene.llf_matched_keys = 0
	bpy.context.scene.llf_csv_data.sources.clear()

def create_animation_sequence():
	pass

def match_shapekey(name:str)->str|None:
	for k in arkit_shapekeys:
		# print("matching key %s to name %s", k, name)
		if k == name:
			# print("match: %s", k)
			return k
		else : pass
	return None

def importcsvtodict(filepath)->dict:	
	csv_file = open(filepath)
	reader = csv.DictReader(csv_file)
	fieldnames = reader.fieldnames
	names = [name[0].lower()+name[1:] for name in fieldnames]
	csv_dict = dict()
	for key in names:
		csv_dict[key] = list()
	for row in reader:
		for k in fieldnames:
			csv_dict[k[0].lower()+k[1:]].append(row[k])	
	return dict(csv_dict)

class LoadCSVFileToMemory(bpy.types.Operator):
	bl_idname = "anim.loadcsvfiletomemory"
	bl_label = "Load CSV to Memory"
	bl_description = "Load Live Link Face CSV file to memory"
	bl_options = {"REGISTER"}

	@classmethod
	def poll(cls, context):
		return True

	def execute(self, context):
		def calc_frames(dictionary)->int:
			for key in dictionary:
				# print(key)
				return dictionary[key]
			raise IndexError
		context.scene.llf_frames = 0
		context.scene.llf_sources = 0
		context.scene.llf_csv_data.sources.clear()
		if Path(context.scene.llf_csv_filepath).exists:
			csv_data_dict = dict()
			csv_data_dict = importcsvtodict(Path(context.scene.llf_csv_filepath))
		context.scene.llf_sources = len(csv_data_dict.keys())-1
		context.scene.llf_frames = len(calc_frames(csv_data_dict))

		for key in csv_data_dict.keys():
			if key.lower() == 'timecode' or key.lower() == 'shapecount':
				pass

			else:
				# print(key)
				source = context.scene.llf_csv_data.sources.add()
				source.name = key
				for value in csv_data_dict[key]:
					# print(value)
					frame = source.frames.add()
					frame.value = float(value)

		return {"FINISHED"}


class FindObjectsARKItBlendshapes(bpy.types.Operator):
	bl_idname = "object.find_arkit_blendshapes"
	bl_label = "Find ARKIT Shapekeys"
	bl_description = "Finds objects with keyable ARKIT blendshapes"
	bl_options = {"REGISTER"}

	@classmethod
	def poll(cls, context):
		return True

	def execute(self, context):
		context.scene.llf_matched_keys = 0
		context.scene.llf_arkit_data.shape_keys.clear()
		for obj in context.selected_objects:
			if obj.type in ('MESH', 'CURVE') and obj.data.shape_keys != None:
				shpk = obj.data.shape_keys
				# print(shpk.name)
				if hasattr(obj.data.shape_keys, "key_blocks"):
					shape_key_data = context.scene.llf_arkit_data.shape_keys.add()
					shape_key_data.name = shpk.name
					for sk in obj.data.shape_keys.key_blocks:
						# print(sk.name)
						match_arkit_shapekey = match_shapekey(sk.name)
						
						if  match_arkit_shapekey:
							# print('match:')
							key_block = shape_key_data.key_blocks.add()
							key_block.name = sk.name
							context.scene.llf_matched_keys += 1

					else : pass
		return {"FINISHED"}
	
class CSVDataToAnimationKeys(bpy.types.Operator):
	bl_idname = "anim.data_to_animation"
	bl_label = "Keyframe CSV data"
	bl_description = "This operator creates key frames based on loaded CSV Data"
	bl_options = {"REGISTER", "UNDO"}

	@classmethod
	def poll(cls, context):
		return True

	def execute(self, context):
		csv_data_dict = context.scene.llf_csv_data.sources
		shape_keys = context.scene.llf_arkit_data.shape_keys
		# for every frame
		for frame in range(context.scene.llf_frames):			
			# print(matched_shapekeys_dict.keys())
			# go trough every matched shape key and animate them
			for key in shape_keys.keys():
				# print(shape_keys[key])
				key_blocks = shape_keys[key].key_blocks
				for kb in key_blocks.keys():
					print(kb)
					# set value for shape key and add keyframe it
					value = csv_data_dict[kb].frames[frame].value
					key_block = bpy.data.shape_keys[key].key_blocks[kb]
					key_block.value = value
					key_block.keyframe_insert(data_path="value", frame=frame+1)
			# go trough head and eyes and add animations
			# ,HeadYaw,HeadPitch,HeadRoll,LeftEyeYaw,LeftEyePitch,LeftEyeRoll,RightEyeYaw,RightEyePitch,RightEyeRoll
			# print(csv_data_dict.keys())
			if context.scene.llf_head_bone:
				bone = context.scene.llf_armature.pose.bones[context.scene.llf_head_bone]
				rotation_quaternion = Euler((
					csv_data_dict["headPitch"].frames[frame].value,
					csv_data_dict["headRoll"].frames[frame].value,
					csv_data_dict["headYaw"].frames[frame].value
				)).to_quaternion()
				bone.rotation_quaternion = rotation_quaternion
				bone.keyframe_insert(data_path="rotation_quaternion", frame=frame+1)

			
			if context.scene.llf_left_eye:
				bone = context.scene.llf_armature.pose.bones[context.scene.llf_left_eye]
				rotation_quaternion = Euler((
					csv_data_dict["leftEyePitch"].frames[frame].value,
					csv_data_dict["leftEyeRoll"].frames[frame].value,
					csv_data_dict["leftEyeYaw"].frames[frame].value
				)).to_quaternion()
				bone.rotation_quaternion = rotation_quaternion
				bone.keyframe_insert(data_path="rotation_quaternion", frame=frame+1)

			if context.scene.llf_right_eye:
				bone = context.scene.llf_armature.pose.bones[context.scene.llf_right_eye]
				rotation_quaternion = Euler((
					csv_data_dict["rightEyePitch"].frames[frame].value,
					csv_data_dict["rightEyeRoll"].frames[frame].value,
					csv_data_dict["rightEyeYaw"].frames[frame].value
				)).to_quaternion()
				bone.rotation_quaternion = rotation_quaternion
				bone.keyframe_insert(data_path="rotation_quaternion", frame=frame+1)

		return {"FINISHED"}


class SimpleLiveLinkFaceCSVImporter_PT_sidebar(bpy.types.Panel):
	bl_idname = "LLFTools_PT_Panel"
	bl_label = "Live Link Face CSV Import to Animation Keys"
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_category = "Tool"

	def draw(self, context):
		layout = self.layout
		row = layout.row()
		row.prop_search(context.scene, "llf_armature", context.scene, "objects", text="Control Rig")
		if context.scene.llf_armature:
			row = layout.row()
			row.prop_search(context.scene, "llf_head_bone", context.scene.llf_armature.pose, "bones", text="Head")
			row = layout.row()
			row.prop_search(context.scene, "llf_left_eye", context.scene.llf_armature.pose, "bones", text="Left eye")
			row = layout.row()
			row.prop_search(context.scene, "llf_right_eye", context.scene.llf_armature.pose, "bones", text="Right eye")
		row = layout.row()
		row.operator(FindObjectsARKItBlendshapes.bl_idname)
		row = layout.row()
		row.label(text='Found Shape keys: '+ str(context.scene.llf_matched_keys))
		row = layout.row()
		row.prop(context.scene, "llf_csv_filepath", text="CSV File")
		row = layout.row()
		row.operator(LoadCSVFileToMemory.bl_idname)
		if context.scene.llf_frames > 0:
			row = layout.row()
			row.label(text='Frames: '+ str(context.scene.llf_frames))
			row.label(text='Data sources: '+ str(context.scene.llf_sources))
		row.operator(CSVDataToAnimationKeys.bl_idname, text="", icon='RECORD_ON')


def register():
	bpy.types.Scene.llf_csv_filepath = csv_filepath
	bpy.types.Scene.llf_frames = csv_frames
	bpy.types.Scene.llf_sources = csv_sources
	bpy.types.Scene.llf_matched_keys = matched_keys
	bpy.types.Scene.llf_armature = armature
	bpy.types.Scene.llf_head_bone = head_bone
	bpy.types.Scene.llf_left_eye = left_eye 
	bpy.types.Scene.llf_right_eye = right_eye
	bpy.app.handlers.load_post.append(llf_load_post_handler)
	bpy.utils.register_class(CSVDataToAnimationKeys)
	bpy.utils.register_class(FindObjectsARKItBlendshapes)
	bpy.utils.register_class(LoadCSVFileToMemory)
	bpy.utils.register_class(SimpleLiveLinkFaceCSVImporter_PT_sidebar)
	bpy.utils.register_class(CSV_Data)
	bpy.types.Scene.llf_csv_data = bpy.props.PointerProperty(type=CSV_Data)
	bpy.utils.register_class(ARKIT_Data)
	bpy.types.Scene.llf_arkit_data = bpy.props.PointerProperty(type=ARKIT_Data)

def unregister():
	bpy.utils.unregister_class(SimpleLiveLinkFaceCSVImporter_PT_sidebar)
	bpy.utils.unregister_class(FindObjectsARKItBlendshapes)
	bpy.utils.unregister_class(CSVDataToAnimationKeys)
	bpy.utils.unregister_class(LoadCSVFileToMemory)
	del bpy.types.Scene.llf_csv_filepath
	del bpy.types.Scene.llf_matched_keys
	del	bpy.types.Scene.llf_head_bone
	del bpy.types.Scene.llf_left_eye
	del bpy.types.Scene.llf_right_eye
	del bpy.types.Scene.llf_armature
	del bpy.types.Scene.llf_frames
	del bpy.types.Scene.llf_sources
	del bpy.types.Scene.llf_csv_data
	del bpy.types.Scene.llf_arkit_data
	bpy.utils.unregister_class(CSV_Data_Frames)
	bpy.utils.unregister_class(CSV_Data_Keys)
	bpy.utils.unregister_class(CSV_Data)
	bpy.utils.unregister_class(ARKIT_Key_Block)
	bpy.utils.unregister_class(ARKIT_Shape_Keys)
	bpy.utils.unregister_class(ARKIT_Data)
	bpy.app.handlers.load_post.remove(llf_load_post_handler)


if __name__ == "__main__":
	register()
