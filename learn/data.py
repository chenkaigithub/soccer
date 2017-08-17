import csv
import os

import pickle

from learn.settings import *
from learn.utils import *


def from_file():
	file_path = os.path.join(DATA_DIR, DATA_SOURCE_FILE)
	print('Loading data from file {}...'.format(file_path))
	with open(file_path) as fin:
		reader = csv.reader(fin)
		feature_set_raw= []
		labels_raw = []
		for i, row in enumerate(reader):
			# ignore the first 2 header lines
			if i == 0 or i == 1:
				continue

			# data cleaning
			def _convert(string):
				try:
					number = float(string)
				except:
					number = np.nan
				return number

			features = row[2:15]
			label = row[19]

			# ignore useless dataset: data without a result
			if label is '':
				continue

			features = list(map(_convert, features))
			feature_set_raw.append(features)
			labels_raw.append(int(label))

	feature_set = np.asarray(feature_set_raw, dtype=np.float32)
	labels = convert_one_hot(np.asarray(labels_raw, dtype=np.float32), NUM_LABELS)
	print('Data successfully loaded with dataset of shape {} and labels of shape {}'.format(feature_set.shape, labels.shape))
	print()
	return feature_set, labels


def save(dataset, labels):
	file_path = os.path.join(DATA_DIR, DATA_SAVE_FILE)
	print('Saving data into {}...'.format(file_path))
	with open(file_path, 'wb') as fout:
		save = {
			'dataset': dataset,
			'labels': labels
		}
		pickle.dump(save, fout, pickle.HIGHEST_PROTOCOL)
	print('Data successfully saved')
	print()


def divide(dataset, labels):
	"""
	Divide dataset into 50% of training set, 25% of validation set,
	and 25% of test set
	"""
	size = dataset.shape[0]
	train_size = size // 2
	valid_size = size // 4
	train_dataset = dataset[:train_size]
	train_labels = labels[:train_size]
	valid_dataset = dataset[train_size:train_size + valid_size]
	valid_labels = labels[train_size:train_size + valid_size]
	test_dataset = dataset[train_size + valid_size: ]
	test_labels = labels[train_size + valid_size: ]

	print('Division complete')
	print('Training set: {} {}'.format(train_dataset.shape, train_labels.shape))
	print('Validation set: {} {}'.format(valid_dataset.shape, valid_labels.shape))
	print('Test set: {} {}'.format(test_dataset.shape, test_labels.shape))
	print()

	return train_dataset, train_labels, valid_dataset, valid_labels, test_dataset, test_labels
