 function subplot(args)
*
* returns the xl, xh, yl, yh position of a subplot
* args(1) = number of rows
* args(2) = number of columns
* args(3) = plot number; starting from top-left, in a row-major order
*		(convension is same as MATLAB's subplot() function)
*
* optional arguments
* args(4) = Scale to gap between plots in x direciton (defauls gap = 0.75);
*	    Defalut value to this argument is 1.0
* args(5) = Scale to gap between plots in y direciton (defauls gap = 0.75)
*	    Defalut value to this argument is 1.0
* args(6) = Scale to the left margine length (defalut value = 1.0);
*	    Defalut value to this argument is 1.0
* args(7) = Scale to the bottom margine length (defalut value = 1.0);
*	    Defalut value to this argument is 1.0
* args(8) = Scale to the right margine length (defalut value = 0.5);
*	    Defalut value to this argument is 1.0
* args(9) = Scale to the top margine length (defalut value = 1.0);
*	    Defalut value to this argument is 1.0
* args(10) = Scale to the x-width of the subplot;
*	     Defalut value to this argument is 1.0
* args(11) = Scale to the y-width of the subplot;
*	     Defalut value to this argument is 1.0

* author: Arindam C <arch@caos.iisc.ernet.in>
* 11/04/2002


*=======================================================================
 if(args = '-help' | args = ' -help' | args = '-help ' | args = ' -help ')
  helpf()
  return
 endif

 if(args = '')
  helps()
  return
 endif

 nrow = subwrd(args,1)
 ncol = subwrd(args,2)
 nplt = subwrd(args,3)

 if(nrow = '' | ncol = '' | nplt = '')
  helps()
  return
 endif

 if(nrow*ncol < nplt)
  say 'subplot: plot number out of range.'
  helps()
  return
 endif

 sgx = subwrd(args,4)
 if(sgx = '');sgx = 1.0; endif;

 sgy = subwrd(args,5)
 if(sgy = '');sgy = 1.0; endif;

 slmar = subwrd(args,6)
 if(slmar = '');slmar = 1.0; endif;

 sbmar = subwrd(args,7)
 if(sbmar = '');sbmar = 1.0; endif;

 srmar = subwrd(args,8)
 if(srmar = '');srmar = 1.0; endif;

 stmar = subwrd(args,9)
 if(stmar = '');stmar = 1.0; endif;

 sxplt = subwrd(args,10)
 if(sxplt = '');sxplt = 1.0; endif;

 syplt = subwrd(args,11)
 if(syplt = '');syplt = 1.0; endif;

* get window information
 'q gxinfo'
 line = sublin(result,2)
 xwin = subwrd(line,4)
 ywin = subwrd(line,6)
* say xwin' 'ywin

 if(xwin > ywin)
  landscape = 1; portrait = 0;
 else
  landscape = 0; portrait = 1;
 endif

* set values of left, top, right and bottom margins
 lmar = 0.6; tmar = 0.6; rmar = 0.6; bmar = 0.5;

* set values of gaps between plots
 gx = 0.75; gy = 0.75;

 gx = gx*sgx;
 gy = gy*sgy;
 lmar = lmar*slmar;
 rmar = rmar*srmar;
 bmar = bmar*sbmar;
 tmar = tmar*stmar;

* find the total lengths of plots in x and y directions
 xltot = xwin - lmar - rmar - (ncol-1)*gx
 yltot = ywin - tmar - bmar - (nrow-1)*gy
* say xltot' 'yltot

* get x and y widths of the subplot
 xplt = xltot/ncol;
 yplt = yltot/nrow;

* scale subplot dimension
 xplt = xplt*sxplt;
 yplt = yplt*syplt;

* say xplt' 'yplt

* get the row and column numbers of the subplot
 nplt1 = nplt;
 irow = 1; jcol = nplt1;
 while(nplt1 > ncol)
  nplt1 = nplt1 - ncol;
  jcol = nplt1;
  irow = irow + 1;
 endwhile

* say irow' 'jcol

* find xl, xh, yl, yh of the subplot
 xl = lmar + (jcol-1)*xplt + (jcol-1)*gx;
 yl = bmar + (nrow-irow)*yplt + (nrow-irow)*gy;
 xh = xl + xplt;
 yh = yl + yplt;

 res = xl' 'xh' 'yl' 'yh

* return(res)

*function setpage(xl,xh,yl,yh)
*  setv='set vpage 'xlv' 'xrv' 'ybv' 'ytv
*  setv
  'set grads off'
  'set vpage off'
  setp='set parea 'xl' 'xh' 'yl' 'yh
  setp
  'set grads off'
*return


*=======================================================================
* short help message
 function helps()
  say ''
  say 'usage: subplot nrow ncol plot_number [sgx sgy slmar sbmar srmar stmar]'
  say 'use subplot -help for more information'
 return

*=======================================================================
* full help message
 function helpf()
  say ''
  say 'usage: subplot nrow ncol plot_number [sgx sgy slmar sbmar srmar stmar]'

  say 'subplot() returns the xl, xh, yl, yh position of a subplot.'
  say ''
  say 'Mandatory Arguments:'
  say ' args(1) = number of rows.'
  say ' args(2) = number of columns.'
  say ' args(3) = plot number; starting from top-left, in a row-major order.'
  say '           (convension is same as MATLAB"s subplot() function).'
  say ''
  say 'Optional Arguments:'
  say ' args(4) = Scale to gap between plots in x direciton (defauls gap = 0.75);'
  say '           Defalut value to this argument is 1.0;'
  say ' args(5) = Scale to gap between plots in y direciton (defauls gap = 0.75);'
  say '           Defalut value to this argument is 1.0;'
  say ' args(6) = Scale to the left margine length (defalut value = 1.0);'
  say '           Defalut value to this argument is 1.0;'
  say ' args(7) = Scale to the bottom margine length (defalut value = 1.0);'
  say '           Defalut value to this argument is 1.0;'
  say ' args(8) = Scale to the right margine length (defalut value = 0.5);'
  say '           Defalut value to this argument is 1.0;'
  say ' args(9) = Scale to the top margine length (defalut value = 1.0);'
  say '           Defalut value to this argument is 1.0;'
  say ' args(10) = Scale to the x-width of the subplot;'
  say '            Defalut value to this argument is 1.0;'
  say ' args(11) = Scale to the y-width of the subplot;'
  say '            Defalut value to this argument is 1.0;'
 return
