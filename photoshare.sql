CREATE TABLE Users (
    user_id INT NOT NULL AUTO_INCREMENT,
    gender VARCHAR(6),
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(40) NOT NULL,
    dob DATE NOT NULL,
    hometown VARCHAR(40),
    fname VARCHAR(40) NOT NULL,
    lname VARCHAR(40) NOT NULL,
    PRIMARY KEY(user_id)
);

CREATE TABLE Albums (
    album_id INT AUTO_INCREMENT,
    Name VARCHAR(40) NOT NULL,
    date_of_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_id INT NOT NULL,
    PRIMARY KEY  (album_id),
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

CREATE TABLE Pictures(
    picture_id INT AUTO_INCREMENT,
    user_id INT,
    caption VARCHAR(200), 
    imgdata LONGBLOB, 
    album_id INT NOT NULL,
    PRIMARY KEY (picture_id),
    FOREIGN KEY (user_id) REFERENCES Users (user_id),
    FOREIGN KEY (album_id) REFERENCES Albums(album_id) ON DELETE CASCADE 
);

CREATE TABLE Comments(
    comment_id INT NOT NULL AUTO_INCREMENT, 
    text TEXT NOT NULL,
    date DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_id INT NOT NULL,
    picture_id INT NOT NULL,
    PRIMARY KEY (comment_id),
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE, 
    FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id) ON DELETE CASCADE
);

CREATE TABLE Likes(
    user_id INT NOT NULL,
    picture_id INT NOT NULL,
    PRIMARY KEY (picture_id, user_id),
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id) ON DELETE CASCADE
);

CREATE TABLE Tags(
    tag_id INT,
    name VARCHAR(100),
    PRIMARY KEY (tag_id)
);

CREATE TABLE Tagged(
    photo_id INT,
    tag_id INT,
    PRIMARY KEY(photo_id, tag_id),
    FOREIGN KEY (photo_id) REFERENCES Photos(photo_id),
    FOREIGN KEY (tag_id) REFERENCES Tags(tag_id)
);

CREATE TABLE Friendship (
    UID1 INT NOT NULL,
    UID2 INT NOT NULL,
    CHECK (UID1 <> UID2),
    PRIMARY KEY(UID1, UID2),
    FOREIGN KEY (UID1) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (UID) REFERENCES USers(user_id) ON DELETE CASCADE
);

CREATE ASSERTION Comment-Constraint CHECK (
    NOT EXISTS (
        SELECT * 
        FROM Comments C, Pictures P
        WHERE C.picture_id = P.picture_id 
        AND P.user_id = C.user_id
    )
);