# Optimization of Deep Architectures for EEG Signal Classification: An AutoML Approach Using Evolutionary Algorithms

The processing and classification of electroencephalography (EEG) signals is challenging due to low signal-to-noise ratio and the presence of artifacts. While there are classification techniques based on features extracted from the signal, deep neural networks offer new opportunities to improve accuracy without the need for predefined features. However, deep learning architectures have many hyperparameters that affect performance, and this paper proposes a method to optimize both the hyperparameters and structure of the network. Experimental results show that deep learning architectures optimized by this method are more accurate and energy-efficient than baseline models.

## Requirements

* [*Python 3.6.8*](https://www.python.org/downloads/)
* [*Platypus*](https://github.com/Project-Platypus/Platypus)
* [*Tensorflow 2.4.1*](https://www.tensorflow.org/?hl=es-419)
* [*PostgreSQL 11.5*](https://www.postgresql.org/)

## Usage

First, execute the SQL script (optimization.sql) in the Postgresql database to have the tables.

Then, the following files are used for the optimization of neural networks.

* Optimal_Master_gpu.py
* Optimal_Worker_gpu.py
* Optimal_CNN_optim.py


## Publications

#### Thesis

1. Aquino-Brítez, Diego. Optimización multi-objetivo de arquitecturas de aprendizaje profundo para el procesamiento de señales EEG en plataformas de cómputo heterogéneas. Granada: Universidad de Granada, 2022. [http://hdl.handle.net/10481/75440]

#### Journals

1. Aquino-Brítez, D., Ortiz, A., Ortega, J., León, J., Formoso, M., Gan, J. Q., & Escobar, J. J. (2021). Optimization of deep architectures for eeg signal classification: An automl approach using evolutionary algorithms. Sensors, 21(6), 2096.

## Funding

This work has been funded by:

* Spanish [*Ministerio de Ciencia, Innovación y Universidades*](https://www.ciencia.gob.es/) under grant number PGC2018-098813-B-C31 and PGC2018-098813-B-C32.
* Spanish [*Consejería de Conocimiento Junta de Andalucía*](https://www.juntadeandalucia.es/organismos/universidadinvestigacioneinnovacion.html) under grant number UMA20-FEDERJA-086.
* [*European Regional Development Fund (ERDF)*](https://ec.europa.eu/regional_policy/en/funding/erdf/).

<div style="text-align: right">
  <img src="https://raw.githubusercontent.com/efficomp/Hpmoon/main/docs/logos/miciu.jpg" height="60">
  <img src="https://raw.githubusercontent.com/efficomp/Hpmoon/main/docs/logos/erdf.png" height="60">
</div>

## License

[GNU GPLv3](https://www.gnu.org/licenses/gpl-3.0.md).
