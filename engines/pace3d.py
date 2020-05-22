import logging as log
from pathlib import Path
import csv
import numpy


class Pace3dEngine:
    """ Specific class to handle Pace 3D simulation software from the IDM HS Karlsruhe Germany.
    """
    def __init__(self):
        self.log = log.getLogger(self.__class__.__name__)

    def read_csv_file(self, file: str, delimiter: str = ' ',
                      x_coord_row: int = 0, y_coord_row: int = 1, z_coord_row: int = 2,
                      values_row: int = 3):
        """ Function to read an dat-file-export from the Software Pace3D from IDM HS Karlsruhe

                 Parameters:
                    file (str): filename including path
                    delimiter (str), optional: delimiter used in ascii file
                    x_coord_row (int), optional: row number for x-coordinate (default: 0)
                    y_coord_row (int), optional: row number for y-coordinate (default: 1)
                    z_coord_row (int), optional: row number for z-coordinate (default: 2)
                    values_row (int), optional:  row number for values (default: 3)

                Returns:
                    ndarray(dict)
                """

        try:
            file = Path(file)

            # TODO Check if row fits to given data

            if not file.is_file():
                self.log.error(f'File {file} not found.')
                raise FileNotFoundError

            self.log.info(f'Load Pace3D-Mesh-File: {file}')

            with file.open('r') as csv_file:
                read_csv = csv.reader(csv_file, delimiter=delimiter)

                lines = []

                for row in read_csv:
                    try:
                        # Check if actual row has the needed length
                        if len(row) >= max(x_coord_row, y_coord_row, z_coord_row, values_row) + 1:
                            if z_coord_row != -1:
                                lines.append({'x_coordinate': float(row[x_coord_row]),
                                              'y_coordinate': float(row[y_coord_row]),
                                              'z_coordinate': float(row[z_coord_row]),
                                              'value': float(row[values_row])
                                              })
                            else:
                                lines.append({'x_coordinate': float(row[x_coord_row]),
                                              'y_coordinate': float(row[y_coord_row]),
                                              'z_coordinate': float(row[z_coord_row]),
                                              'value': float(row[values_row])
                                              })
                        else:
                            self.log.info(f'Empty or to short row found. Continue... [{row.__str__()}]')

                    except Exception as err:
                        self.log.info(f'Empty row found or transition failed. Continue... [{err}]')

                self.log.debug(f'{len(lines)} rows read successfully', )

                return lines

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
