import os
import numpy as np
import copy
import re

def extract_vert(filepath):
  with open(filepath, "r") as file:
      # Extract the vertex data from the file
      vertex_data = [line.split()[1:4] for line in file if line.startswith("v ")]
      vertex_array = np.array(vertex_data).astype(dtype="float32")
      vert = np.reshape(vertex_array, (-1, vertex_array.shape[0] * vertex_array.shape[1]))
      return vert


def do_sentence_packing(BASE_DATA_PATH):
  print("3-preformer: sentence-packing start")

  # Create output directory if not exist
  OUTPUT_DIR = os.path.join(BASE_DATA_PATH, "vertices_npy_untrimmed")
  if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
    print(f"Output path {OUTPUT_DIR} created")

  BASE_PATH_RAW = os.path.join(BASE_DATA_PATH, "normalized")

  # Sequential
  # for date_subject in sorted(os.listdir(BASE_PATH_RAW)):
  # Parallel
  date_subject = '20240126_006Vasilisa'
  for scenario_id in sorted(os.listdir(os.path.join(BASE_PATH_RAW, date_subject)), key=lambda x: int(x)):
    # (26, 36), (37, 46), (47, 617), (618, 627), (628, 637)
    if 628 <= int(scenario_id) <= 637:
        pass
    else:
      continue
    print("Processing " + os.path.join(BASE_PATH_RAW, date_subject, scenario_id))
    data_verts = []
    
    for obj in sorted(os.listdir(os.path.join(BASE_PATH_RAW, date_subject, scenario_id)), key=lambda x: int(x.split("_")[-1].split(".")[0])):
      target_obj_path = os.path.join(BASE_PATH_RAW, date_subject, scenario_id, obj)
      verts = extract_vert(target_obj_path)
      print(target_obj_path + ", verts shape: " + str(verts.shape))
      if verts.shape[1] == 24049 * 3:
        data_verts.append(verts)
      else:
        raise Exception("An obj doesn't have the exact number of vertices")
    data_verts = np.array(data_verts)
    data_verts = np.squeeze(data_verts)
    file_name = f"{date_subject}_{scenario_id}.npy"
    file_path = os.path.join(OUTPUT_DIR, file_name)
    np.save(file_path, data_verts)
    print(f"Saved data_verts of shape {data_verts.shape} to {file_path}")

  print("3-preformer: sentence-packing end")

def main():
  BASE_DATA_PATH = '/data6/leoho/vasilisa'
  do_sentence_packing(BASE_DATA_PATH)

if __name__ == "__main__":
  main()