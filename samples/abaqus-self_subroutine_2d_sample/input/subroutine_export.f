!	Language: Fortran 95
!	Compiler: Intel Visual Fortran Compiler
!	Subroutines for Abaqus 2019
!	Date: 2019-11
!	Owner: Sven F. Biebricher - RWTH Aachen, Chair of Geotechnics
!	Project: MERID

!	###########################################
!	UEXTERNALDB
!	###########################################
!	Routine that will be executed on every single event you can imagine.
!	Various execution events are delimited by the parameter analysisPos.
!	In this case the output file (csv-file) will be created and kept open 
!	until the end of the end of the analysis.
	subroutine uExternalDB( analysisPos, lRestart, 
&							time, dTime, kStep, kInc )
		!use, intrinsic :: iso_fortran_env, only: error_unit
		include 'ABA_PARAM.INC'
		

		!	###############################		
		!	Declare SUBROUTINE variables
		!	###############################
		integer, dimension(2) :: time
		integer :: analysisPos, kStep


		!	###############################		
		!	Declare LOCAL variables
		!	###############################
		integer, parameter :: csvOutUnitVoidR = 113
		integer, parameter :: csvOutUnitPoreP = 116
		integer, parameter :: csvOutUnitMatrix = 114
		integer, parameter :: csvInUnitPoreP = 115

		character(256) :: outDir
		integer :: lenOutDir

		character(256) :: jobName
		integer :: lenJobName

		integer :: dateTime(8)
		character(256) :: cDummy

		character(512) :: csvOutFileVoidR	! data output file void ratio
		character(512) :: csvOutFilePoreP	! data output file pore pressure
		character(512) :: csvOutFileMatrix	! mesh output file matrix
		character(512) :: csvInFilePoreP		! data input file pore pressure
		
		write(*,*) '* Subroutine uExternalDB() called!'
		
		!	###############################
		!	USER PRE definitions
		!	###############################
		call getJobName( jobName, lenJobName )

		!	Set output filenames (CSV-Files)
		csvOutFileVoidR = trim(jobName) // '_void-ratio.csv'
		csvOutFilePoreP = trim(jobName) // '_pore-pressure.csv'
		csvOutFileMatrix = trim(jobName) // '_matrix.csv'
		csvInFilePoreP = 'input_pore-pressure.csv'
		
		!	Create filepath + filename and save in fileOut/matrixFile.
		!  As filepath	the actual Abaqus output directory will be used.
		!	Get Abaqus output directory for analysis	
		call getOutDir( outDir, lenOutDir )
		csvOutFileVoidR = outDir(:lenOutDir) // '\' // csvOutFileVoidR
		csvOutFilePoreP = outDir(:lenOutDir) // '\' // csvOutFilePoreP
		csvOutFileMatrix = outDir(:lenOutDir) // '\' // csvOutFileMatrix
		csvInFilePoreP = outDir(:lenOutDir) // '\' // csvInFilePoreP

		isPosition: select case (analysisPos)
		! #####################################
		! BEGINNING of ANALYSIS or RESTARTING
		! #####################################
		case (0, 4) 
			! #######################
			! CSV export void ratio
			! #######################
			! Opening a csv-file once to export pore pressure
			open(unit=csvOutUnitVoidR, file=csvOutFileVoidR, status='unknown',
&						form='formatted')

			! Check if the file was loaded succesfully
			INQUIRE(csvOutUnitVoidR, openED=ISopen)
			if (ISopen) then
					call stdb_AbqERR(1, 'Exportfile (%S) opened succesfully. '
&                    //'If the analysis stops here, the file may be opened'
&                    //'by another process!', 0, 0.0, csvOutFileVoidR)
			else
					call stdb_AbqERR(-2, 'Error opening the exportfile (%S).',
&                    0, 0.0, csvOutFileVoidR)
			end if
			
			! #######################
			! CSV export pore pressure
			! #######################
			! Opening a csv-file once to export void ratio
			open(unit=csvOutUnitPoreP, file=csvOutFilePoreP, status='unknown',
&						form='formatted')

			! Check if the file was loaded succesfully
			INQUIRE(csvOutUnitPoreP, openED=ISopen)
			if (ISopen) then
					call stdb_AbqERR(1, 'Exportfile (%S) opened succesfully. '
&                    //'If the analysis stops here, the file may be opened'
&                    //'by another process!', 0, 0.0, csvOutFilePoreP)
			else
					call stdb_AbqERR(-2, 'Error opening the exportfile (%S).',
&                    0, 0.0, csvOutFilePoreP)
			end if
			
			! #######################
			! CSV export mesh/matrix
			! #######################
			! Opening a csv-file once to export matrix
			open(unit=csvOutUnitMatrix, file=csvOutFileMatrix, status='unknown',
&						form='formatted')

			! Check if the file was loaded succesfully
			INQUIRE(csvOutUnitMatrix, openED=ISopen)
			if (ISopen) then
					call stdb_AbqERR(1, 'Matrixfile (%S) opened succesfully. '
&                    //'If the analysis stops here, the file may be opened'
&                    //'by another process!', 0, 0.0, csvOutFileMatrix)
			else
					call stdb_AbqERR(-2, 'Error opening the matrixfile (%S).',
&                    0, 0.0, csvOutFileMatrix)
			end if

			! Get now()
			call DATE_AND_time( cDummy, cDummy, cDummy, dateTime )

!			! Write jobName into output file
!			write(outFileUnit, '(A, A)') 'Abaqus Job-Name: ', TRIM(jobName)
			
			
			! #######################
			! CSV import pore pressure
			! #######################			
			! Reading pore-pressure-datafile
			open (unit=csvInUnitPoreP, action='read', 
&						file=csvInFilePoreP, iostat=ioError)

			if (ioError /= 0) then
				
				call stdb_AbqERR(-1,'Error reading pore pressure input file (%S). 
&					Error: %I', ioError, 0.0, csvInFilePoreP)		
			
			else
				call stdb_AbqERR(1,'Pore pressure input file (%S) opened successfully.',
&							0, 0.0, csvInFilePoreP)
				
			end if
			
		! #####################################
		! END of ANALYSIS
		! #####################################
		case (3)

			! Get now()
			call DATE_AND_time( cDummy, cDummy, cDummy, dateTime )

			!	Close output files
			close(csvOutUnitVoidR)
			call stdb_AbqERR(1,'CSV export void ratio (%S) closed.', 
&							0, 0.0, csvOutFileVoidR)

			close(csvOutUnitPoreP)
			call stdb_AbqERR(1,'CSV export pore pressure (%S) closed.',
&							0, 0.0, csvOutFilePoreP)
			
			close(csvOutUnitMatrix)
			call stdb_AbqERR(1,'CSV export mesh/matrix (%S) closed.', 
&							0, 0.0, csvOutFileMatrix)
			
			close(csvInUnitPoreP)
			call stdb_AbqERR(1,'CSV import pore pressure (%S) closed.', 
&							0, 0.0, csvInFilePoreP)
			
		end select isPosition


		!	Print analysisPos and time into msg everytime the subroutine is executed
		call stdb_AbqERR(1,'Subroutine uExternalDB() has been executed. 
&                 analysisPos: %I; Time: %R, %R', analysisPos, time,' ')

		return
	end subroutine uExternalDB


!	###########################################
!	URDFIL
!	###########################################
!     Routine to access data in the result-file. It will be called at the
!     end of any increment in which information is written into result-file.
!     In this analysis the subroutine will be used to read void ratio and
!     pore pressure from the result-file based on elements. Only the results
!     (and the coordinates of containing element) of the last increment will
!     be saved into an output file, opened through subroutine UEXTERNALDB
!     at the beginning of the analysis.
	subroutine uRdFil( lStop, lOvrWrt, kStep, kInc, dTime, time)

		include 'ABA_PARAM.INC'

		!	###############################		
		!	Declare SUBROUTINE variables
		!	###############################
	
		integer, dimension(2) :: time
		integer :: lOverWrt
		integer :: kStep, kInc
	
		double precision, dimension(513) :: dpArray
		integer, dimension(nprecd, 513) :: iArray
	
		!	###############################		
		!	Declare LOCAL variables
		!	###############################		
		integer, parameter :: csvOutUnitVoidR = 113
		integer, parameter :: csvOutUnitPoreP = 116
		integer, parameter :: csvOutUnitMatrix = 114
	
		! Array to collect the data that shall be printed into one
		! column in the data-output-file. Size of the array appends
		! on the data to be stored.
		! x, y, z, voidRatio, porePressure
		real, dimension(5) :: writeBuffer =-999
	
		! Interpretation of double precision as integers
		equivalence (dpArray(1), iArray(1,1))
	
		! Overwrite data in fil-file (result-file) in next increment
		lOvrWrt = 1;		

		! The command rewind always jumps back to the beginning of the output file. Thus
		! only the last written increment is saved effectively.
		rewind(csvOutUnitVoidR)
		rewind(csvOutUnitPoreP)
		rewind(csvOutUnitMatrix)
		
		write(*,*) '* Subroutine uRdFil() called!'
		write(*,*) kStep, kInc
		
		! Write headline in data output file
		write(csvOutUnitVoidR, '(A, ", ", A, ", ", A,", ", A)')
&                 'x', 'y', 'z', 'voidRatio'
		write(csvOutUnitPoreP, '(A, ", ", A, ", ", A,", ", A)')
&                 'x', 'y', 'z', 'porePressure'

		! Write headline in matrix file
		write(csvOutUnitMatrix, '(A, ", ", A, ", ", A,", ", A)')
&                 'x', 'y', 'z', 'nodeNo'

		call posFil( kStep, kInc, dpArray, jrdc)
		do
			! Read fil-file
			call dbFile( 0, dpArray, jrdc)
		
			! If jrdc is 1 eof is reached
			if ( jrdc == 1 ) exit
		
			key = iArray(1,2)
			
			! In the following only element based data will be collected from
			! the fil-file for data output file. Included data will be pore 
			! poressure, void ratio and the coordinates of the integration point 
			! of the specific element. Element datasets are printed out sequentially.
			! Therefore the data of an element will be collected first and 
			! afterwards printed out.
			! Node based data will be used to export the matrix of the analysis
			! just once after the first step (geostatic). This export is needed
			! to sync input data (like pore pressure) to the existing matrix and
			! just compare the node numbers, instead of the coordinates. Those 
			! information do not need to be collected as they refer to a single key.
			! Each key represents one output element (see manual).
			isKey: select case (key)
				
				! #####################################
				case (6) ! VOIDRATIO of an ELEMENT
					voidR = dpArray(3)			

					writeBuffer(4) = voidR

		
				! #############################
				case (8) ! COORDINATES of an ELEMENT
					coord_x = dpArray(3)
					coord_y = dpArray(4)
					coord_z = dpArray(5)

					writeBuffer(1) = coord_x
					writeBuffer(2) = coord_y
					writeBuffer(3) = coord_z
			

				! #############################
				case (18)! POREPRESSURE of an ELEMENT
					porePressure = dpArray(3)
				
					writeBuffer(5) = porePressure
			

				! #############################
				! Shall be called just once to export the matrix
				case (107) !  COORDINATES of a NODE
					nodeNo = iArray(1,3)
					coord_x = dpArray(4)
					coord_y = dpArray(5)
					coord_z = dpArray(6)
				
					! node, x, y, z
					write(csvOutUnitMatrix, '(F9.3, ", ", F9.3, ", ", F9.3, ", ",
&								I8)')
&								coord_x, coord_y, coord_z, nodeNo

			end select isKey
				
			! Check whether all data records have been collected.  If 
			! yes, then the data is stored. 	
			if (writeBuffer(1) /= -999 .and. writeBuffer(2) /= -999 .and. 
&				writeBuffer(3) /= -999 .and. writeBuffer(4) /= -999 .and. 
&				writeBuffer(5) /= -999) then
				
				! x, y, z, voidRatio
				write(csvOutUnitVoidR, '(F9.3, ", ", F9.3, ", ", F9.3, ", ",
&							F9.7)') writeBuffer(1),
&							writeBuffer(2), writeBuffer(3), writeBuffer(4)

				! x, y, z, porePressure
				write(csvOutUnitPoreP, '(F9.3, ", ", F9.3, ", ", F9.3, ", ",
&							F12.2)') writeBuffer(1),
&							writeBuffer(2), writeBuffer(3), writeBuffer(5)
			
				! Reset the writebuffer
				writeBuffer = -999
				
			end if
		
		end do
	
		return
	end subroutine uRdFil

