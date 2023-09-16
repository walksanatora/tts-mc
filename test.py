import json
dims = 5
top = [[[None for z in range(dims)] for y in range(dims)] for x in range(dims)]
top[2][2][2] = 32
print(json.dumps(top,indent=2))