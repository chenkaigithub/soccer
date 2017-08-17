import learn.data as data
import learn.model as model

dataset, labels = data.from_file()

model.fully_connected(dataset, labels, [20, 40, 60, 20, 12, 6], 50001)
