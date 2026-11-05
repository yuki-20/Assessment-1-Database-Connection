-- Optional IBM Db2 path: execute once in your own writable schema.
-- Then import data/cardio_train_raw.csv with delimiter ; and header enabled.
-- AGE remains in days. Do not remove outliers before reproducing the lab queries.
CREATE TABLE CARDIO_TRAIN (
    ID INTEGER NOT NULL PRIMARY KEY,
    AGE INTEGER NOT NULL,
    GENDER SMALLINT NOT NULL CHECK (GENDER IN (1, 2)),
    HEIGHT INTEGER NOT NULL,
    WEIGHT DOUBLE NOT NULL,
    AP_HI INTEGER NOT NULL,
    AP_LO INTEGER NOT NULL,
    CHOLESTEROL SMALLINT NOT NULL CHECK (CHOLESTEROL IN (1, 2, 3)),
    GLUC SMALLINT NOT NULL CHECK (GLUC IN (1, 2, 3)),
    SMOKE SMALLINT NOT NULL CHECK (SMOKE IN (0, 1)),
    ALCO SMALLINT NOT NULL CHECK (ALCO IN (0, 1)),
    ACTIVE SMALLINT NOT NULL CHECK (ACTIVE IN (0, 1)),
    CARDIO SMALLINT NOT NULL CHECK (CARDIO IN (0, 1))
);
