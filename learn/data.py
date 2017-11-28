import csv
import os
import pickle

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from download.storage import Game
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


def save_hand_data(dataset, labels):
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
    print('Test set: {} {}\n'.format(test_dataset.shape, test_labels.shape))

    return train_dataset, train_labels, valid_dataset, valid_labels, test_dataset, test_labels


def db_url(port=None):
    url_base = '{dialect}+{driver}://{username}:{password}@{host}{port}/{db}?charset=utf8'
    if port is not None:
        port = ':' + str(port)
    url = url_base.format(
        dialect='mysql', driver='mysqldb',
        username=DB_USER, password=DB_PASS,
        host=DB_HOST, db=DB_NAME, port=port)
    return url


def connect_db(echo=False):
    url = db_url(3306)
    engine = create_engine(url, echo=echo)
    Session = sessionmaker(bind=engine)
    return engine, Session


def get_trends_dir(flat):
    folder = "flat" if flat else "tile"
    return os.path.join(DATA_DIR, 'trends', folder)


def get_saved(flat):
    trends_dir = get_trends_dir(flat)
    if not os.path.exists(trends_dir):
        print("Directory {} doesn't exist, creating...".format(trends_dir))
        os.mkdir(trends_dir)

    saved = []
    for file_name in os.listdir(trends_dir):
        if file_name.startswith('.'):
            continue
        base = os.path.basename(file_name)
        base = '.'.join(base.split('.')[:-1])
        if len(base):
            saved.append(base)
    return saved


def download_from_db(flat=True):
    # 初始化数据库连接
    engine, Session = connect_db()
    session = Session()

    # 获取本地已存数据
    saved = get_saved(flat)

    # 获取所有完整比赛
    print('正在从数据库提取球赛数据...')
    games = session.query(Game).filter(Game.host_score != None, Game.guest_score != None).order_by(Game.serial).all()
    print('成功提取{}场球赛数据'.format(len(games)))

    current_date = None
    current_dataset = []
    current_labels = []
    for game in games:
        game_date = game.date()
        # 跳过已存数据
        if game_date in saved:
            continue

        data = construct_data(game, flat)
        if data is None:
            continue

        if current_date != game_date:
            if current_date is not None:
                current_dataset = np.asarray(current_dataset)
                labels = convert_one_hot(np.asarray(current_labels), 8)
                save(
                    dataset=current_dataset,
                    labels=labels,
                    file_name=current_date
                )
            current_date = game_date
            current_dataset = []
            current_labels = []

        current_dataset.append(data)
        result, result_with_concede = get_results(game)
        label = get_label(result, result_with_concede)
        current_labels.append(label)

    if len(current_dataset) != 0:
        current_dataset = np.asarray(current_dataset)
        labels = convert_one_hot(np.asarray(current_labels), 8)
        save(dataset=current_dataset, labels=labels, file_name=current_date)


def construct_data(game, flat=True):
    trends = game.points
    num_trends = TREND_MAX_HOUR * 12
    if len(trends) < num_trends:
        return None
    trends = trends[-num_trends : ]
    wins, draws, loses = [i.win for i in trends], [i.draw for i in trends], [i.lose for i in trends]
    cwins, cdraws, closes = [i.cwin for i in trends], [i.cdraw for i in trends], [i.close for i in trends]

    tiled = np.array([wins, draws, loses, cwins, cdraws, closes], dtype=np.float32)
    if flat:
        flattened = tiled.flatten()
        return np.insert(flattened, 0, [game.concede, game.endorse])
    # return tiled data in some format
    return None


def save(dataset, labels, file_name):
    file_name += '.pickle'
    file_path = os.path.join(get_trends_dir(flat=True), file_name)
    print("Saving {} sets of data into file {}...".format(len(dataset), file_name))
    with open(file_path, 'wb') as fout:
        save = {
            'dataset': dataset,
            'labels': labels
        }
        pickle.dump(save, fout, pickle.HIGHEST_PROTOCOL)
    print('Data successfully saved\n')


def get_results(game):
    '''
    若主队胜则输出2, 平则输出1, 负则输出0
    '''
    if game.host_score > game.guest_score:
        result = 2
    elif game.host_score == game.guest_score:
        result = 1
    else:
        result = 0
    if game.host_score + game.concede > game.guest_score:
        with_concede = 2
    elif game.host_score + game.concede == game.guest_score:
        with_concede = 1
    else:
        with_concede = 0
    return result, with_concede


def get_label(result, result_with_concede):
    label = result * 3 + result_with_concede
    if label > 4:
        label -= 1
    return label


def extract_trends_data(path, flat=True):
    if not path.startswith(os.path.join(DATA_DIR, 'trends')):
        shape = 'flat' if flat else 'tile'
        path = os.path.join(DATA_DIR, 'trends', shape, path)
    with open(path, 'rb') as fin:
        data = pickle.load(fin)
    return data


def feed_trends_data(batch_size):
    saved = get_saved(True)
    for date in saved:
        file_name = date + '.pickle'
        data = extract_trends_data(file_name, True)
        dataset = data['dataset']
        labels = data['labels']
        print('长度', dataset.shape[0])
        for i in range(0, dataset.shape[0], batch_size):
            print(i, i+batch_size)


def get_dataset(flat=True):
    if flat:
        saved = get_saved(flat)
        data_stack = None
        label_stack = None
        for date in saved:
            file_name = date + '.pickle'
            data = extract_trends_data(file_name)
            dataset = data['dataset']
            labels = data['labels']
            if data_stack is None:
                data_stack = dataset
                label_stack = labels
            else:
                data_stack = np.vstack([data_stack, dataset])
                label_stack = np.vstack([label_stack, labels])
        return data_stack, label_stack
    else:
        return None, None


if __name__ == '__main__':
    # a = feed_trends_data(5)
    # for i in range(5):
    #   data = next(a)
    #   print(data)

    download_from_db()
    # feed_trends_data(5)



