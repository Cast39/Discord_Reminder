import pickle, time

with open(input("filename: "), "rb") as f:
	save = pickle.load(f)
