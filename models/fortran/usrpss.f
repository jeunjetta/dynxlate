C     USRPSS -- stabilizer with washout and lookup-table gain
C     (deliberately contains constructs OUTSIDE the supported subset:
C      DATA table + DO loop -- exercises the manual-review path)
C
C     CON(J)   = TW     (sec) washout time constant
C     CON(J+1) = KS     (pu) stabilizer gain
C     CON(J+2) = VSMAX  (pu) output max
C     CON(J+3) = VSMIN  (pu) output min
C
C     STATE(K) = WASH  washout state
C
      SUBROUTINE USRPSS (MC, ISLOT)
      INCLUDE 'COMON4.INS'
      INTEGER MC, ISLOT, J, K, N
      REAL GTAB(5)
      DATA GTAB /0.5, 0.8, 1.0, 1.2, 1.5/
      J = STRTIN(1, ISLOT)
      K = STRTIN(3, ISLOT)
      IF (MODE .EQ. 1) THEN
         STATE(K) = SPEED(MC)
      ELSE IF (MODE .EQ. 2) THEN
         DSTATE(K) = (SPEED(MC) - STATE(K)) / CON(J)
      ELSE IF (MODE .EQ. 3) THEN
         G = CON(J+1)
         DO 10 N = 1, 5
            G = G * GTAB(N)
   10    CONTINUE
         VOTHSG(MC) = AMIN1(AMAX1(G * (SPEED(MC) - STATE(K)),
     &      CON(J+3)), CON(J+2))
      ENDIF
      RETURN
      END
