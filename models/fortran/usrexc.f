C     USREXC -- simplified excitation system (SEXS-like) user model
C
C     CON(J)   = TR    (sec) voltage filter time constant
C     CON(J+1) = K     (pu) regulator gain
C     CON(J+2) = TE    (sec) exciter time constant
C     CON(J+3) = EMIN  (pu) minimum field voltage
C     CON(J+4) = EMAX  (pu) maximum field voltage
C
C     STATE(K)   = VSENS  sensed terminal voltage
C     STATE(K+1) = EFDS   exciter output state
C
C     VAR(L)   = VERR  voltage error
C
      SUBROUTINE USREXC (MC, ISLOT)
      INCLUDE 'COMON4.INS'
      INTEGER MC, ISLOT, J, K, L
      J = STRTIN(1, ISLOT)
      K = STRTIN(3, ISLOT)
      L = STRTIN(4, ISLOT)
      IF (MODE .EQ. 1) THEN
         STATE(K) = ETERM(MC)
         STATE(K+1) = EFD(MC)
         VAR(L) = VREF(MC) - ETERM(MC)
      ELSE IF (MODE .EQ. 2) THEN
         VAR(L) = VREF(MC) - ETERM(MC) + VOTHSG(MC)
         DSTATE(K) = (VAR(L) - STATE(K)) / CON(J)
         DSTATE(K+1) = (CON(J+1) * STATE(K) - STATE(K+1)) / CON(J+2)
      ELSE IF (MODE .EQ. 3) THEN
         EFD(MC) = AMIN1(AMAX1(STATE(K+1), CON(J+3)), CON(J+4))
      ENDIF
      RETURN
      END
