import logging as log
from pathlib import Path
import csv
import numpy


class Pace3dEngine:

    def __init__(self):
        self.log = log.getLogger(self.__class__.__name__)

    def read_csv_file(self, file: str, delimiter: str = ' '):
        """ Function to read an dat-file-export from the Software Pace3D from IDM HS Karlsruhe

         Parameters:
            file (str): filename including path
            delimiter (str), optional: delimiter used in ascii file

        Returns:
            ndarray
        """

        try:
            file = Path(file)

            if not file.is_file():
                self.log.error(f'File {file} not found.')
                raise FileNotFoundError

            self.log.info(f'Load Pace3D-File: {file}')

            with file.open('r') as csv_file:
                read_csv = csv.reader(csv_file, delimiter=delimiter)

                x = []
                y = []
                z = []
                data_set = []

                for row in read_csv:
                    try:
                        x.append(float(row[0]))
                        y.append(float(row[1]))
                        z.append(float(row[2]))
                        data_set.append(float(row[3]))

                    except Exception as err:
                        self.log.debug('Empty row found and ignored. Continue... [%s]', str(err))

                self.log.info(f'{len(data_set)} rows read successfully')

                return numpy.array([x, y, z, data_set])

        except Exception as err:
            self.log.error(f'File --{file}-- could not be read correctly [{err}]')
            return 0

    def write_csv_file(self, data_array, file, delimiter: str = ' '):
        """ Function to write an csv-file-input from a given ndarray for the Software Pace3D

         Parameters:
            data_array (ndarray): data set
            file (str): filename including path
            delimiter (str), optional: delimiter used in ascii file

        Returns:
            boolean
        """

        try:

            file = Path(file)

            if not Path(file.parent[0]).is_dir():
                self.log.error(f'Path to save file into {file.parent[0]} not found.')
                raise FileNotFoundError

            self.log.info(f'Write pace3D-data-file: {file}')

            # Writing data to csv-file
            numpy.savetxt(file, data_array, delimiter=delimiter, fmt='%i %i %f')

            return True

        except Exception as err:
            self.log.error(f'Writing data in  --{file}-- not successful. [{err}]')
            return False
