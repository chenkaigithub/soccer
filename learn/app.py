import learn.data as data

# dataset, labels = data.from_file()
#
# model.fully_connected(dataset, labels, [20, 40, 60, 20, 12, 6], 50001)
from learn.data import download_from_db

if __name__ == '__main__':
	download_from_db()