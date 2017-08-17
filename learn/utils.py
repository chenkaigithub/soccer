import numpy as np


def convert_one_hot(array, num_labels):
	return (np.arange(num_labels) == array[:, None]).astype(np.float32)


def accuracy(predictions, labels):
	return (
		100 * np.sum(
			np.argmax(predictions, 1) == np.argmax(labels, 1)
		) / predictions.shape[0])