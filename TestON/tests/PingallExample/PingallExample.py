"""
Description: This test is an example of a simple single node ONOS test

List of test cases:
CASE1: Compile ONOS and push it to the test machine
CASE2: Assign mastership to controller
CASE3: Pingall
"""
class PingallExample:

    def __init__( self ):
        self.default = ''
        
    def CASE1( self, main ):
        import threading
        import time
        import Queue
        """
           CASE1 is to compile ONOS and push it to the test machines

           Startup sequence:
           git pull
           mvn clean install
           onos-package
           cell <name>
           onos-verify-cell
           onos-install -f
           onos-wait-for-start
        """
        desc = "ONOS Single node cluster restart HA test - initialization"
        main.log.report( desc )
        main.case( "Setting up test environment" )

        # load some vairables from the params file
        PULLCODE = False
        if main.params[ 'Git' ] == 'True':
            PULLCODE = True
        cellName = main.params[ 'ENV' ][ 'cellName' ]

        ONOS1Ip = main.params[ 'CTRL' ][ 'ip1' ]
        ONOS2Ip = main.params[ 'CTRL' ][ 'ip2' ]
        ONOS3Ip = main.params[ 'CTRL' ][ 'ip3' ]

        main.step( "Applying cell variable to environment" )
        cellResult = main.ONOSbench.setCell( cellName )
        verifyResult = main.ONOSbench.verifyCell()

        main.log.report( "Uninstalling ONOS" )
        #main.ONOSbench.onosUninstall( ONOS1Ip )

        cleanInstallResult = main.TRUE
        gitPullResult = main.TRUE

        main.step( "Compiling the latest version of ONOS" )
        if PULLCODE:
            main.step( "Git checkout and pull master" )
            main.ONOSbench.gitCheckout( "master" )
            gitPullResult = main.ONOSbench.gitPull()

            main.step( "Using mvn clean & install" )
            cleanInstallResult = main.TRUE
            if gitPullResult == main.TRUE:
                cleanInstallResult = main.ONOSbench.cleanInstall()
            else:
                main.log.warn( "Did not pull new code so skipping mvn " +
                               "clean install" )
        main.ONOSbench.getVersion( report=True )

        cellResult = main.ONOSbench.setCell( cellName )
        verifyResult = main.ONOSbench.verifyCell()
        main.step( "Creating ONOS package" )
        packageResult = main.ONOSbench.onosPackage()

        main.step( "Installing ONOS package" )
        onos1InstallResult = main.FALSE
        
        main.log.info("Running thread")
        
        time1 = time.time()
        q1 = Queue.Queue()
        q2 = Queue.Queue()
        q3 = Queue.Queue()
        pool = []
        CLI1 = (main.ONOScli1.startOnosCli,  ONOS1Ip, q1)
        CLI2 = (main.ONOScli2.startOnosCli, ONOS2Ip, q2)
        CLI3 = (main.ONOScli3.startOnosCli, ONOS3Ip, q3)
       
        CLItoRun = [CLI1,CLI2,CLI3]
        i = 0
        for  cli,ip,q in CLItoRun:
            t = threading.Thread(target = cli, args=[ip,q])
            pool.append(t)
            t.start()
        
        
        """
        # This is how you create threads
        # threadName = threading.Thread(target = main.<componentName>.<methodName>, args
        # = [...args to pass... ]>)
        t1 = threading.Thread(target=main.ONOScli1.startOnosCli, args= [ONOS1Ip, q1])
        t2 = threading.Thread(target=main.ONOScli2.startOnosCli, args= [ONOS2Ip, q2])
        t3 = threading.Thread(target=main.ONOScli3.startOnosCli, args= [ONOS3Ip, q3])
        pool.append(t1)
        pool.append(t2)
        pool.append(t3)
        
        for thread in pool:
            thread.start()
        """
        #then we join all the threads in the pool which simply letting all the
        #threads to finish to move on to the code
        for thread in pool:
            thread.join()
        time2 = time.time()
        if q1.get()==main.TRUE and q2.get() == main.TRUE and q3.get()==main.TRUE:
            main.log.info( "Successful CLI startup!!!")
        else:
            main.log.info("ONOS CLI did not start up properly")
            main.cleanup()
            main.exit()
        
        main.log.info("Time for connecting to CLI: %2f seconds" %(time2 - time1))

        main.step( "Checking if ONOS is up yet" )
        for i in range( 2 ):
            onos1Isup = main.ONOSbench.isup( ONOS1Ip )
            if onos1Isup:
                break
        if not onos1Isup:
            main.log.report( "ONOS1 didn't start!" )

        # TODO: if it becomes an issue, we can retry this step  a few times

        cliResult = main.ONOScli1.startOnosCli( ONOS1Ip )

        case1Result = ( cleanInstallResult and packageResult and
                        cellResult and verifyResult and
                        onos1Isup and cliResult )

        utilities.assert_equals( expect=main.TRUE, actual=case1Result,
                                 onpass="Test startup successful",
                                 onfail="Test startup NOT successful" )

        if case1Result == main.FALSE:
            main.cleanup()
            main.exit()
        
        # Starting the mininet using the old way
        main.step( "Starting Mininet ..." )
        netIsUp = main.Mininet1.startNet()
        if netIsUp:
            main.log.info("Mininet CLI is up")
        else:
            main.log.info("Mininet CLI is down")

    def CASE2( self, main ):
        """
           Assign mastership to controller
        """
        import re

        main.log.report( "Assigning switches to controller" )
        main.case( "Assigning Controller" )
        main.step( "Assign switches to controller" )

        ONOS1Ip = main.params[ 'CTRL' ][ 'ip1' ]
        ONOS1Port = main.params[ 'CTRL' ][ 'port1' ]

        for i in range( 1, 14 ):
            main.Mininet1.assignSwController(
                sw=str( i ),
                ip1=ONOS1Ip,
                port1=ONOS1Port )

        mastershipCheck = main.TRUE
        for i in range( 1, 14 ):
            response = main.Mininet1.getSwController( "s" + str( i ) )
            try:
                main.log.info( str( response ) )
            except:
                main.log.info( repr( response ) )
            if re.search( "tcp:" + ONOS1Ip, response ):
                mastershipCheck = mastershipCheck and main.TRUE
            else:
                mastershipCheck = main.FALSE
        if mastershipCheck == main.TRUE:
            main.log.report( "Switch mastership assigned correctly" )
        utilities.assert_equals(
            expect=main.TRUE,
            actual=mastershipCheck,
            onpass="Switch mastership assigned correctly",
            onfail="Switches not assigned correctly to controllers" )

    def CASE3( self, main ):
        """
           Assign intents
        """
        import time

        main.log.report( "Run Pingall" )
        main.case( "Run Pingall" )

        # install onos-app-fwd
        main.log.info( "Install reactive forwarding app" )
        main.ONOScli1.featureInstall( "onos-app-fwd" )

        # REACTIVE FWD test
        pingResult = main.FALSE
        time1 = time.time()
        pingResult = main.Mininet1.pingall()
        time2 = time.time()
        main.log.info( "Time for pingall: %2f seconds" % ( time2 - time1 ) )

        # uninstall onos-app-fwd
        main.log.info( "Uninstall reactive forwarding app" )
        main.ONOScli1.featureUninstall( "onos-app-fwd" )

        utilities.assert_equals( expect=main.TRUE, actual=pingResult,
                                 onpass="All hosts are reachable",
                                 onfail="Some pings failed" )
