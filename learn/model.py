import tensorflow as tf

import learn.data as data
from learn.settings import *
from learn.utils import *

batch_size = 16

alpha = .001
beta = 0.01

def fully_connected_deprecated(dataset, labels, hidden_size):
	train_dataset, train_labels, \
	valid_dataset, valid_labels, \
	test_dataset, test_labels = data.divide(dataset, labels)

	graph = tf.Graph()
	with graph.as_default():

		# input data for training
		tf_train_dataset = tf.placeholder(tf.float32,
		                                  shape=(batch_size, FEATURE_SIZE))
		tf_train_labels = tf.placeholder(tf.float32, shape=(batch_size, NUM_LABELS))

		tf_valid_dataset = tf.constant(valid_dataset)
		tf_test_dataset = tf.constant(test_dataset)

		theta_1 = tf.Variable(tf.truncated_normal([FEATURE_SIZE, hidden_size]))
		biases_1 = tf.Variable(tf.zeros([hidden_size]))

		theta_2 = tf.Variable(tf.truncated_normal([hidden_size, NUM_LABELS]))
		biases_2 = tf.Variable(tf.zeros(NUM_LABELS))

		logits_1 = tf.matmul(tf_train_dataset, theta_1) + biases_1
		hidden_layer = tf.nn.relu(logits_1)
		logits_2 = tf.matmul(hidden_layer, theta_2) + biases_2

		regularizer = tf.nn.l2_loss(theta_1) + tf.nn.l2_loss(theta_2)
		loss = tf.reduce_mean(
			tf.nn.softmax_cross_entropy_with_logits(logits=logits_2, labels=tf_train_labels)
		) + beta * regularizer

		optimizer = tf.train.GradientDescentOptimizer(alpha).minimize(loss)

		train_prediction = tf.nn.softmax(logits_2)

		logits_1 = tf.matmul(tf_valid_dataset, theta_1) + biases_1
		hidden_layer = tf.nn.relu(logits_1)
		logits_2 = tf.matmul(hidden_layer, theta_2) + biases_2
		valid_prediction = tf.nn.softmax(logits_2)

		logits_1 = tf.matmul(tf_test_dataset, theta_1) + biases_1
		hidden_layer = tf.nn.relu(logits_1)
		logits_2 = tf.matmul(hidden_layer, theta_2) + biases_2
		test_prediction = tf.nn.softmax(logits_2)

	# num_steps = train_labels.shape[0] // batch_size
	num_steps = 60001

	with tf.Session(graph=graph) as session:
		tf.global_variables_initializer().run()
		print("Initialization complete, start iterations...")
		for step in range(num_steps):
			offset = (step * batch_size) % (train_labels.shape[0] - batch_size)
			batch_data = train_dataset[offset:offset+batch_size, :]
			batch_labels = train_labels[offset:offset+batch_size, :]
			feed = {
				tf_train_dataset: batch_data,
				tf_train_labels: batch_labels
			}
			_, cost, predictions = session.run(
				[optimizer, loss, train_prediction],
				feed_dict=feed
			)
			if step % 2000 == 0:
				print('Mini batch loss at step {}: {:.1f}'.format(step, cost))
				print('Training accuracy: {:.1f}%'.format(accuracy(predictions, batch_labels)))
				print('Validation accuracy: {:.1f}%'.format(accuracy(valid_prediction.eval(), valid_labels)))
				print()
		print('Training complete!')
		print('Test accuracy: {:.1f}%'.format(accuracy(test_prediction.eval(), test_labels)))

	return theta_1, biases_1, theta_2, biases_2


def fully_connected(dataset, labels, neurons, iterations=4001):
	train_dataset, train_labels, \
	valid_dataset, valid_labels, \
	test_dataset, test_labels = data.divide(dataset, labels)
	feature_size = train_dataset.shape[1]
	num_labels = train_labels.shape[1]
	hidden_layers = len(neurons)

	graph = tf.Graph()
	with graph.as_default():

		tf_train_dataset = tf.placeholder(tf.float32,
		                                  shape=(batch_size, feature_size))
		tf_train_labels = tf.placeholder(tf.float32, shape=(batch_size, num_labels))

		tf_valid_dataset = tf.constant(valid_dataset)
		tf_test_dataset = tf.constant(test_dataset)

		theta_list = []
		bias_list = []
		n = feature_size
		for layer in range(hidden_layers + 1):
			if layer < hidden_layers:
				l = neurons[layer]
			else:
				l = num_labels
			theta = tf.Variable(tf.truncated_normal([n, l], stddev=.1))
			biase = tf.Variable(tf.constant(1.0, shape=[l]))
			theta_list.append(theta)
			bias_list.append(biase)
			n = l

		def forward_prop(training_data):
			for layer in range(hidden_layers):
				hypo = tf.matmul(training_data, theta_list[layer]) + bias_list[layer]
				logits = tf.nn.relu(hypo)
				training_data = logits

			logits = tf.matmul(training_data, theta_list[hidden_layers]) + bias_list[hidden_layers]
			return logits

		logits = forward_prop(tf_train_dataset)

		regularizer = 0
		for theta in theta_list:
			regularizer += tf.nn.l2_loss(theta)
		loss = tf.reduce_mean(
			tf.nn.softmax_cross_entropy_with_logits(
				logits=logits,
				labels=tf_train_labels
			)
		) + beta * regularizer

		optimizer = tf.train.GradientDescentOptimizer(alpha).minimize(loss)

		train_prediction = tf.nn.softmax(logits)

		valid_logits = forward_prop(tf_valid_dataset)
		valid_prediction = tf.nn.softmax(valid_logits)

		test_logits = forward_prop(tf_test_dataset)
		test_prediction = tf.nn.softmax(test_logits)

	with tf.Session(graph=graph) as session:
		tf.global_variables_initializer().run()
		print('Initialization complete, start training...')
		for step in range(iterations):
			offset = (step * batch_size) % (train_labels.shape[0] - batch_size)
			batch_data = train_dataset[offset:offset + batch_size, :]
			batch_labels = train_labels[offset:offset + batch_size, :]
			feed = {
				tf_train_dataset: batch_data,
				tf_train_labels: batch_labels
			}
			_, cost, predictions = session.run(
				[optimizer, loss, train_prediction],
				feed_dict=feed
			)

			if step % (iterations // 10) == 0:
				print('Mini batch loss at step {}: {:.1f}'.format(step, cost))
				print('Training accuracy: {:.1f}%'.format(accuracy(predictions, batch_labels)))
				print('Validation accuracy: {:.1f}%'.format(accuracy(valid_prediction.eval(), valid_labels)))
				print()
		print('Training complete!')
		print('Test accuracy: {:.1f}%'.format(accuracy(test_prediction.eval(), test_labels)))

	return theta_list, bias_list
