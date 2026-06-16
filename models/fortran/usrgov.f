C     USRGOV -- TGOV1-like turbine governor user model
C
C     CON(J)   = R     (pu) permanent droop
C     CON(J+1) = T1    (sec) governor time constant
C     CON(J+2) = VMIN  (pu) minimum valve position
C     CON(J+3) = VMAX  (pu) maximum valve position
C     CON(J+4) = T2    (sec) lead time constant
C     CON(J+5) = T3    (sec) lag time constant
C     CON(J+6) = DT    (pu) turbine damping
C
C     STATE(K)   = PVALVE  valve position state
C     STATE(K+1) = PLL     lead-lag state
C
C     VAR(L)   = PREF  power reference
C
      SUBROUTINE USRGOV (MC, ISLOT)
      INCLUDE 'COMON4.INS'
      INTEGER MC, ISLOT, J, K, L
      J = STRTIN(1, ISLOT)
      K = STRTIN(3, ISLOT)
      L = STRTIN(4, ISLOT)
      IF (MODE .EQ. 1) THEN
         STATE(K) = PMECH(MC)
         STATE(K+1) = PMECH(MC)
         VAR(L) = PMECH(MC) * CON(J)
      ELSE IF (MODE .EQ. 2) THEN
         DSTATE(K) = ((VAR(L) - SPEED(MC)) / CON(J) - STATE(K)) / CON(J+1)
         IF (STATE(K) .GT. CON(J+3)) STATE(K) = CON(J+3)
         IF (STATE(K) .LT. CON(J+2)) STATE(K) = CON(J+2)
         DSTATE(K+1) = (STATE(K) - STATE(K+1)) / CON(J+5)
      ELSE IF (MODE .EQ. 3) THEN
         PMECH(MC) = STATE(K+1) + CON(J+4) / CON(J+5) * (STATE(K) -
     &      STATE(K+1)) - CON(J+6) * SPEED(MC)
      ENDIF
      RETURN
      END
