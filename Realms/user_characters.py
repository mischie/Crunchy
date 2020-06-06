from datetime import datetime, timedelta

from realms.character import Character


class UserCharacters:
    """
        Object representing a user's characters, this system can
        be modified to expand to fit anything that is needed which
        will likely be the case as this system is developed.
        This also handles all DB interactions and self contains it.
        :returns UserCharacters object:
    """

    def __init__(self, user_id, rolls, expires_in, callback, database=None):
        """
        :param user_id:
        :param rolls:
        :param callback:
        :param database: -> Optional
        If data is None it falls back to a global var,
        THIS ONLY EXISTS WHEN RUNNING THE FILE AS MAIN!
        """
        self.user_id = user_id
        self._db = db if database is None else database
        data = self._db.get_characters(user_id=user_id)

        self.characters = data.pop('characters', [])  # Emergency safe guard
        self.rank = data.pop('rank', {'ranking': 0, 'power': 0, 'total_character': 0})
        self._rolls = rolls
        self._expires_in = expires_in
        self.mod_callback = callback

    def submit_character(self, character: Character):
        if len(self.characters) > 0:
            self.characters.append(character.to_dict())
            self._db.update_characters(self.user_id, self.characters)
        else:
            self.characters.append(character.to_dict())
            self._db.add_characters(self.user_id,
                                    {'characters': self.characters, 'rank': self.rank})

    def dump_character(self, character: Character):
        id_ = character.id
        for i, character_ in enumerate(self.characters):
            if character_['id'] == id_:
                self.characters.pop(i)
        if len(self.characters) > 0:
            self._db.update_characters(self.user_id, self.characters)
        else:
            self._db.reset_characters(user_id=self.user_id)
        return self.characters

    def update_rolls(self, modifier: int):
        self._rolls += modifier
        if self.rolls_left <= 0:
            self._expires_in = datetime.now() + timedelta(hours=12)
        self.mod_callback(self.user_id, self)

    @property
    def rolls_left(self):
        return self._rolls

    def get_time_obj(self):
        return self._expires_in

    @property
    def expires_in(self):
        if self._expires_in is not None:
            delta = self._expires_in - datetime.now()
            hours, seconds = divmod(delta.total_seconds(), 3600)
            minutes, seconds = divmod(seconds, 60)
            return f"{int(hours)}h, {int(minutes)}m, {int(seconds)}s"
        return self._expires_in

    def _generate_block(self):
        """ This turns a list of X amount of side into 10 block chunks. """
        pages, rem = divmod(len(self.characters), 10)
        chunks, i = [], 0
        for i in range(0, pages, 10):
            chunks.append(self.characters[i:i + 10])
        if rem != 0:
            chunks.append(self.characters[i:i + rem])
        return chunks

    def get_blocks(self):
        """ A generator to allow the bot to paginate large sets. """
        for block in self._generate_block():
            yield block

    @property
    def amount_of_items(self):
        return len(self.characters)
