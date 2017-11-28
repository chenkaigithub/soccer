# dataset, labels = data.from_file()
#
# model.fully_connected(dataset, labels, [20, 40, 60, 20, 12, 6], 50001)
from learn import data
from learn import model

if __name__ == '__main__':
	dataset, labels = data.get_dataset()
	model.fully_connected_(dataset, labels, [20, 40, 60, 20, 16], 100001)