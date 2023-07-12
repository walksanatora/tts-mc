import pickle

with open("config", "rb") as cfg:
    print(pickle.load(cfg))
