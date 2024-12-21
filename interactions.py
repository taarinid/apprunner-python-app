import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

class Interactions:
    """Encapsulates an Amazon DynamoDB table of movie data.

    Example data structure for a movie record in this table:
        {
            "phone": "4082349456",
            "name": Jeffrey,
            "received_message": "My business idea is selling peanuts in Kampala",
            "mentor_type": "refugee",
            "sent_message": "You need to do amrket research on peanuts market in Uganda",
            "timestamp": "12-21-24 10:19:23 UTC"
        }
    """

    def __init__(self, dyn_resource, logger=None):
        """
        :param dyn_resource: A Boto3 DynamoDB resource.
        """
        self.dyn_resource = dyn_resource
        self.logger = logger
        # The table variable is set during the scenario in the call to
        # 'exists' if the table exists. Otherwise, it is set by 'create_table'.
        self.table = None


    def exists(self, table_name):
        """
        Determines whether a table exists. As a side effect, stores the table in
        a member variable.

        :param table_name: The name of the table to check.
        :return: True when the table exists; otherwise, False.
        """
        try:
            table = self.dyn_resource.Table(table_name)
            table.load()
            exists = True
        except ClientError as err:
            if err.response["Error"]["Code"] == "ResourceNotFoundException":
                exists = False
            else:
                self.logger.error(
                    "Couldn't check for existence of %s. Here's why: %s: %s",
                    table_name,
                    err.response["Error"]["Code"],
                    err.response["Error"]["Message"],
                )
                raise
        else:
            self.table = table
        return exists


    def create_table(self, table_name):
        """
        Creates an Amazon DynamoDB table that can be used to store movie data.
        The table uses the release year of the movie as the partition key and the
        title as the sort key.

        :param table_name: The name of the table to create.
        :return: The newly created table.
        """
        try:
            self.table = self.dyn_resource.create_table(
                TableName=table_name,
                KeySchema=[
                    {"AttributeName": "phone", "KeyType": "HASH"},  # Partition key
                    {"AttributeName": "timestamp", "KeyType": "RANGE"},  # Sort key
                ],
                AttributeDefinitions=[
                    {"AttributeName": "phone", "AttributeType": "S"},
                    {"AttributeName": "timestamp", "AttributeType": "S"},
                ],
                ProvisionedThroughput={
                    "ReadCapacityUnits": 10,
                    "WriteCapacityUnits": 10,
                },
            )
            self.table.wait_until_exists()
        except ClientError as err:
            self.logger.error(
                "Couldn't create table %s. Here's why: %s: %s",
                table_name,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise
        else:
            return self.table


    def list_tables(self):
        """
        Lists the Amazon DynamoDB tables for the current account.

        :return: The list of tables.
        """
        try:
            tables = []
            for table in self.dyn_resource.tables.all():
                print(table.name)
                tables.append(table)
        except ClientError as err:
            self.logger.error(
                "Couldn't list tables. Here's why: %s: %s",
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise
        else:
            return tables


    # def write_batch(self, movies):
    #     """
    #     Fills an Amazon DynamoDB table with the specified data, using the Boto3
    #     Table.batch_writer() function to put the items in the table.
    #     Inside the context manager, Table.batch_writer builds a list of
    #     requests. On exiting the context manager, Table.batch_writer starts sending
    #     batches of write requests to Amazon DynamoDB and automatically
    #     handles chunking, buffering, and retrying.

    #     :param movies: The data to put in the table. Each item must contain at least
    #                    the keys required by the schema that was specified when the
    #                    table was created.
    #     """
    #     try:
    #         with self.table.batch_writer() as writer:
    #             for movie in movies:
    #                 writer.put_item(Item=movie)
    #     except ClientError as err:
    #         logger.error(
    #             "Couldn't load data into table %s. Here's why: %s: %s",
    #             self.table.name,
    #             err.response["Error"]["Code"],
    #             err.response["Error"]["Message"],
    #         )
    #         raise


    def add_interaction(self, phone, timestamp, received_message, sent_message, mentor_type, name):
        """
        Adds an interaction to the table.

        :param phone: The phone number.
        :param timestamp: timestamp of the interaction.
        :param received_message: The message received.
        :param sent_message: The message sent from AI.
        :param mentor_type: Refugee/Local/AI
        :param name: The name of the person.
        """
        try:
            self.table.put_item(
                Item={
                    "phone": phone,
                    "timestamp": timestamp,
                    "received_message": received_message,
                    "sent_message": sent_message,
                    "mentor_type": mentor_type,
                    "name": name,
                }
            )
        except ClientError as err:
            self.logger.error(
                "Couldn't add interaction %s, %s, %s to the table %s because %s and %s",
                phone,
                timestamp,
                name,
                self.table.name,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise


    # def get_movie(self, title, year):
    #     """
    #     Gets movie data from the table for a specific movie.

    #     :param title: The title of the movie.
    #     :param year: The release year of the movie.
    #     :return: The data about the requested movie.
    #     """
    #     try:
    #         response = self.table.get_item(Key={"year": year, "title": title})
    #     except ClientError as err:
    #         logger.error(
    #             "Couldn't get movie %s from table %s. Here's why: %s: %s",
    #             title,
    #             self.table.name,
    #             err.response["Error"]["Code"],
    #             err.response["Error"]["Message"],
    #         )
    #         raise
    #     else:
    #         return response["Item"]


    # def update_movie(self, title, year, rating, plot):
    #     """
    #     Updates rating and plot data for a movie in the table.

    #     :param title: The title of the movie to update.
    #     :param year: The release year of the movie to update.
    #     :param rating: The updated rating to the give the movie.
    #     :param plot: The updated plot summary to give the movie.
    #     :return: The fields that were updated, with their new values.
    #     """
    #     try:
    #         response = self.table.update_item(
    #             Key={"year": year, "title": title},
    #             UpdateExpression="set info.rating=:r, info.plot=:p",
    #             ExpressionAttributeValues={":r": Decimal(str(rating)), ":p": plot},
    #             ReturnValues="UPDATED_NEW",
    #         )
    #     except ClientError as err:
    #         logger.error(
    #             "Couldn't update movie %s in table %s. Here's why: %s: %s",
    #             title,
    #             self.table.name,
    #             err.response["Error"]["Code"],
    #             err.response["Error"]["Message"],
    #         )
    #         raise
    #     else:
    #         return response["Attributes"]


    def query_interactions(self, phone):
        """
        Queries for interactions by phone number. 

        :param phone: phone number.
        :return: The list of interactions by phone number.
        """
        try:
            response = self.table.query(KeyConditionExpression=Key("phone").eq(phone))
        except ClientError as err:
            self.logger.error(
                "Couldn't query for interactions by %s. Here's why: %s %s",
                phone,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise
        else:
            return response["Items"]


    # def scan_movies(self, year_range):
    #     """
    #     Scans for movies that were released in a range of years.
    #     Uses a projection expression to return a subset of data for each movie.

    #     :param year_range: The range of years to retrieve.
    #     :return: The list of movies released in the specified years.
    #     """
    #     movies = []
    #     scan_kwargs = {
    #         "FilterExpression": Key("year").between(
    #             year_range["first"], year_range["second"]
    #         ),
    #         "ProjectionExpression": "#yr, title, info.rating",
    #         "ExpressionAttributeNames": {"#yr": "year"},
    #     }
    #     try:
    #         done = False
    #         start_key = None
    #         while not done:
    #             if start_key:
    #                 scan_kwargs["ExclusiveStartKey"] = start_key
    #             response = self.table.scan(**scan_kwargs)
    #             movies.extend(response.get("Items", []))
    #             start_key = response.get("LastEvaluatedKey", None)
    #             done = start_key is None
    #     except ClientError as err:
    #         logger.error(
    #             "Couldn't scan for movies. Here's why: %s: %s",
    #             err.response["Error"]["Code"],
    #             err.response["Error"]["Message"],
    #         )
    #         raise

    #     return movies


    # def delete_movie(self, title, year):
    #     """
    #     Deletes a movie from the table.

    #     :param title: The title of the movie to delete.
    #     :param year: The release year of the movie to delete.
    #     """
    #     try:
    #         self.table.delete_item(Key={"year": year, "title": title})
    #     except ClientError as err:
    #         logger.error(
    #             "Couldn't delete movie %s. Here's why: %s: %s",
    #             title,
    #             err.response["Error"]["Code"],
    #             err.response["Error"]["Message"],
    #         )
    #         raise


    def delete_table(self):
        """
        Deletes the table.
        """
        try:
            self.table.delete()
            self.table = None
        except ClientError as err:
            logger.error(
                "Couldn't delete table. Here's why: %s: %s",
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise




