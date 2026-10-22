var dZ="179",h8={LEFT:0,MIDDLE:1,RIGHT:2,ROTATE:0,DOLLY:1,PAN:2},b8={ROTATE:0,PAN:1,DOLLY_PAN:2,DOLLY_ROTATE:3},mZ=0,CQ=1,uZ=2;var wQ=1,cZ=2,K8=3,x8=0,b0=1,o0=2,g8=0,Y6=1,_Q=2,IQ=3,PQ=4,nZ=5,S9=100,sZ=101,oZ=102,iZ=103,aZ=104,rZ=200,tZ=201,eZ=202,JW=203,QW=204,$W=205,ZW=206,WW=207,HW=208,YW=209,XW=210,KW=211,UW=212,GW=213,qW=214,Q7=0,$7=1,Z7=2,X6=3,W7=4,H7=5,Y7=6,X7=7,EW=0,NW=1,OW=2,z8=0,FW=1,RW=2,kW=3,MW=4,DW=5,LW=6,VW=7;var j9=301,W9=302,K7=303,U7=304,K6=306,y9=1000,G7=1001,q7=1002,B8=1003,E7=1004;var H9=1005;var Z8=1006,v9=1007;var C8=1008;var p8=1009,zW=1010,BW=1011,U6=1012,TQ=1013,f9=1014,l8=1015,G6=1016,AQ=1017,SQ=1018,h9=1020,CW=35902,wW=1021,_W=1022,U8=1023,N7=1026,q6=1027,IW=1028,jQ=1029,PW=1030,yQ=1031;var vQ=1033,O7=33776,F7=33777,R7=33778,k7=33779,fQ=35840,hQ=35841,bQ=35842,xQ=35843,gQ=36196,pQ=37492,lQ=37496,dQ=37808,mQ=37809,uQ=37810,cQ=37811,nQ=37812,sQ=37813,oQ=37814,iQ=37815,aQ=37816,rQ=37817,tQ=37818,eQ=37819,J$=37820,Q$=37821,M7=36492,$$=36494,Z$=36495,TW=36283,W$=36284,H$=36285,Y$=36286;var X$=2300,D7=2301;var K$=0,E6=1,b9=2;var AW=3201;var SW=0,jW=1,Y9="",d8="srgb",P0="srgb-linear",U$="linear",W0="srgb";var yW=512,vW=513,fW=514,G$=515,hW=516,bW=517,xW=518,gW=519;var q$="300 es",E$=2000;class w8{addEventListener(J,Q){if(this._listeners===void 0)this._listeners={};let $=this._listeners;if($[J]===void 0)$[J]=[];if($[J].indexOf(Q)===-1)$[J].push(Q)}hasEventListener(J,Q){let $=this._listeners;if($===void 0)return!1;return $[J]!==void 0&&$[J].indexOf(Q)!==-1}removeEventListener(J,Q){let $=this._listeners;if($===void 0)return;let Z=$[J];if(Z!==void 0){let W=Z.indexOf(Q);if(W!==-1)Z.splice(W,1)}}dispatchEvent(J){let Q=this._listeners;if(Q===void 0)return;let $=Q[J.type];if($!==void 0){J.target=this;let Z=$.slice(0);for(let W=0,H=Z.length;W<H;W++)Z[W].call(this,J);J.target=null}}}var z0=["00","01","02","03","04","05","06","07","08","09","0a","0b","0c","0d","0e","0f","10","11","12","13","14","15","16","17","18","19","1a","1b","1c","1d","1e","1f","20","21","22","23","24","25","26","27","28","29","2a","2b","2c","2d","2e","2f","30","31","32","33","34","35","36","37","38","39","3a","3b","3c","3d","3e","3f","40","41","42","43","44","45","46","47","48","49","4a","4b","4c","4d","4e","4f","50","51","52","53","54","55","56","57","58","59","5a","5b","5c","5d","5e","5f","60","61","62","63","64","65","66","67","68","69","6a","6b","6c","6d","6e","6f","70","71","72","73","74","75","76","77","78","79","7a","7b","7c","7d","7e","7f","80","81","82","83","84","85","86","87","88","89","8a","8b","8c","8d","8e","8f","90","91","92","93","94","95","96","97","98","99","9a","9b","9c","9d","9e","9f","a0","a1","a2","a3","a4","a5","a6","a7","a8","a9","aa","ab","ac","ad","ae","af","b0","b1","b2","b3","b4","b5","b6","b7","b8","b9","ba","bb","bc","bd","be","bf","c0","c1","c2","c3","c4","c5","c6","c7","c8","c9","ca","cb","cc","cd","ce","cf","d0","d1","d2","d3","d4","d5","d6","d7","d8","d9","da","db","dc","dd","de","df","e0","e1","e2","e3","e4","e5","e6","e7","e8","e9","ea","eb","ec","ed","ee","ef","f0","f1","f2","f3","f4","f5","f6","f7","f8","f9","fa","fb","fc","fd","fe","ff"],YZ=1234567,W6=Math.PI/180,Q9=180/Math.PI;function Q8(){let J=Math.random()*4294967295|0,Q=Math.random()*4294967295|0,$=Math.random()*4294967295|0,Z=Math.random()*4294967295|0;return(z0[J&255]+z0[J>>8&255]+z0[J>>16&255]+z0[J>>24&255]+"-"+z0[Q&255]+z0[Q>>8&255]+"-"+z0[Q>>16&15|64]+z0[Q>>24&255]+"-"+z0[$&63|128]+z0[$>>8&255]+"-"+z0[$>>16&255]+z0[$>>24&255]+z0[Z&255]+z0[Z>>8&255]+z0[Z>>16&255]+z0[Z>>24&255]).toLowerCase()}function xJ(J,Q,$){return Math.max(Q,Math.min($,J))}function N$(J,Q){return(J%Q+Q)%Q}function RY(J,Q,$,Z,W){return Z+(J-Q)*(W-Z)/($-Q)}function kY(J,Q,$){if(J!==Q)return($-J)/(Q-J);else return 0}function H6(J,Q,$){return(1-$)*J+$*Q}function MY(J,Q,$,Z){return H6(J,Q,1-Math.exp(-$*Z))}function DY(J,Q=1){return Q-Math.abs(N$(J,Q*2)-Q)}function LY(J,Q,$){if(J<=Q)return 0;if(J>=$)return 1;return J=(J-Q)/($-Q),J*J*(3-2*J)}function VY(J,Q,$){if(J<=Q)return 0;if(J>=$)return 1;return J=(J-Q)/($-Q),J*J*J*(J*(J*6-15)+10)}function zY(J,Q){return J+Math.floor(Math.random()*(Q-J+1))}function BY(J,Q){return J+Math.random()*(Q-J)}function CY(J){return J*(0.5-Math.random())}function wY(J){if(J!==void 0)YZ=J;let Q=YZ+=1831565813;return Q=Math.imul(Q^Q>>>15,Q|1),Q^=Q+Math.imul(Q^Q>>>7,Q|61),((Q^Q>>>14)>>>0)/4294967296}function _Y(J){return J*W6}function IY(J){return J*Q9}function PY(J){return(J&J-1)===0&&J!==0}function TY(J){return Math.pow(2,Math.ceil(Math.log(J)/Math.LN2))}function AY(J){return Math.pow(2,Math.floor(Math.log(J)/Math.LN2))}function SY(J,Q,$,Z,W){let{cos:H,sin:Y}=Math,X=H($/2),K=Y($/2),U=H((Q+Z)/2),G=Y((Q+Z)/2),q=H((Q-Z)/2),E=Y((Q-Z)/2),F=H((Z-Q)/2),k=Y((Z-Q)/2);switch(W){case"XYX":J.set(X*G,K*q,K*E,X*U);break;case"YZY":J.set(K*E,X*G,K*q,X*U);break;case"ZXZ":J.set(K*q,K*E,X*G,X*U);break;case"XZX":J.set(X*G,K*k,K*F,X*U);break;case"YXY":J.set(K*F,X*G,K*k,X*U);break;case"ZYZ":J.set(K*k,K*F,X*G,X*U);break;default:console.warn("THREE.MathUtils: .setQuaternionFromProperEuler() encountered an unknown order: "+W)}}function J8(J,Q){switch(Q.constructor){case Float32Array:return J;case Uint32Array:return J/4294967295;case Uint16Array:return J/65535;case Uint8Array:return J/255;case Int32Array:return Math.max(J/2147483647,-1);case Int16Array:return Math.max(J/32767,-1);case Int8Array:return Math.max(J/127,-1);default:throw new Error("Invalid component type.")}}function aJ(J,Q){switch(Q.constructor){case Float32Array:return J;case Uint32Array:return Math.round(J*4294967295);case Uint16Array:return Math.round(J*65535);case Uint8Array:return Math.round(J*255);case Int32Array:return Math.round(J*2147483647);case Int16Array:return Math.round(J*32767);case Int8Array:return Math.round(J*127);default:throw new Error("Invalid component type.")}}var X9={DEG2RAD:W6,RAD2DEG:Q9,generateUUID:Q8,clamp:xJ,euclideanModulo:N$,mapLinear:RY,inverseLerp:kY,lerp:H6,damp:MY,pingpong:DY,smoothstep:LY,smootherstep:VY,randInt:zY,randFloat:BY,randFloatSpread:CY,seededRandom:wY,degToRad:_Y,radToDeg:IY,isPowerOfTwo:PY,ceilPowerOfTwo:TY,floorPowerOfTwo:AY,setQuaternionFromProperEuler:SY,normalize:aJ,denormalize:J8};class PJ{constructor(J=0,Q=0){PJ.prototype.isVector2=!0,this.x=J,this.y=Q}get width(){return this.x}set width(J){this.x=J}get height(){return this.y}set height(J){this.y=J}set(J,Q){return this.x=J,this.y=Q,this}setScalar(J){return this.x=J,this.y=J,this}setX(J){return this.x=J,this}setY(J){return this.y=J,this}setComponent(J,Q){switch(J){case 0:this.x=Q;break;case 1:this.y=Q;break;default:throw new Error("index is out of range: "+J)}return this}getComponent(J){switch(J){case 0:return this.x;case 1:return this.y;default:throw new Error("index is out of range: "+J)}}clone(){return new this.constructor(this.x,this.y)}copy(J){return this.x=J.x,this.y=J.y,this}add(J){return this.x+=J.x,this.y+=J.y,this}addScalar(J){return this.x+=J,this.y+=J,this}addVectors(J,Q){return this.x=J.x+Q.x,this.y=J.y+Q.y,this}addScaledVector(J,Q){return this.x+=J.x*Q,this.y+=J.y*Q,this}sub(J){return this.x-=J.x,this.y-=J.y,this}subScalar(J){return this.x-=J,this.y-=J,this}subVectors(J,Q){return this.x=J.x-Q.x,this.y=J.y-Q.y,this}multiply(J){return this.x*=J.x,this.y*=J.y,this}multiplyScalar(J){return this.x*=J,this.y*=J,this}divide(J){return this.x/=J.x,this.y/=J.y,this}divideScalar(J){return this.multiplyScalar(1/J)}applyMatrix3(J){let Q=this.x,$=this.y,Z=J.elements;return this.x=Z[0]*Q+Z[3]*$+Z[6],this.y=Z[1]*Q+Z[4]*$+Z[7],this}min(J){return this.x=Math.min(this.x,J.x),this.y=Math.min(this.y,J.y),this}max(J){return this.x=Math.max(this.x,J.x),this.y=Math.max(this.y,J.y),this}clamp(J,Q){return this.x=xJ(this.x,J.x,Q.x),this.y=xJ(this.y,J.y,Q.y),this}clampScalar(J,Q){return this.x=xJ(this.x,J,Q),this.y=xJ(this.y,J,Q),this}clampLength(J,Q){let $=this.length();return this.divideScalar($||1).multiplyScalar(xJ($,J,Q))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this}negate(){return this.x=-this.x,this.y=-this.y,this}dot(J){return this.x*J.x+this.y*J.y}cross(J){return this.x*J.y-this.y*J.x}lengthSq(){return this.x*this.x+this.y*this.y}length(){return Math.sqrt(this.x*this.x+this.y*this.y)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)}normalize(){return this.divideScalar(this.length()||1)}angle(){return Math.atan2(-this.y,-this.x)+Math.PI}angleTo(J){let Q=Math.sqrt(this.lengthSq()*J.lengthSq());if(Q===0)return Math.PI/2;let $=this.dot(J)/Q;return Math.acos(xJ($,-1,1))}distanceTo(J){return Math.sqrt(this.distanceToSquared(J))}distanceToSquared(J){let Q=this.x-J.x,$=this.y-J.y;return Q*Q+$*$}manhattanDistanceTo(J){return Math.abs(this.x-J.x)+Math.abs(this.y-J.y)}setLength(J){return this.normalize().multiplyScalar(J)}lerp(J,Q){return this.x+=(J.x-this.x)*Q,this.y+=(J.y-this.y)*Q,this}lerpVectors(J,Q,$){return this.x=J.x+(Q.x-J.x)*$,this.y=J.y+(Q.y-J.y)*$,this}equals(J){return J.x===this.x&&J.y===this.y}fromArray(J,Q=0){return this.x=J[Q],this.y=J[Q+1],this}toArray(J=[],Q=0){return J[Q]=this.x,J[Q+1]=this.y,J}fromBufferAttribute(J,Q){return this.x=J.getX(Q),this.y=J.getY(Q),this}rotateAround(J,Q){let $=Math.cos(Q),Z=Math.sin(Q),W=this.x-J.x,H=this.y-J.y;return this.x=W*$-H*Z+J.x,this.y=W*Z+H*$+J.y,this}random(){return this.x=Math.random(),this.y=Math.random(),this}*[Symbol.iterator](){yield this.x,yield this.y}}class A0{constructor(J=0,Q=0,$=0,Z=1){this.isQuaternion=!0,this._x=J,this._y=Q,this._z=$,this._w=Z}static slerpFlat(J,Q,$,Z,W,H,Y){let X=$[Z+0],K=$[Z+1],U=$[Z+2],G=$[Z+3],q=W[H+0],E=W[H+1],F=W[H+2],k=W[H+3];if(Y===0){J[Q+0]=X,J[Q+1]=K,J[Q+2]=U,J[Q+3]=G;return}if(Y===1){J[Q+0]=q,J[Q+1]=E,J[Q+2]=F,J[Q+3]=k;return}if(G!==k||X!==q||K!==E||U!==F){let M=1-Y,N=X*q+K*E+U*F+G*k,O=N>=0?1:-1,C=1-N*N;if(C>Number.EPSILON){let w=Math.sqrt(C),v=Math.atan2(w,N*O);M=Math.sin(M*v)/w,Y=Math.sin(Y*v)/w}let L=Y*O;if(X=X*M+q*L,K=K*M+E*L,U=U*M+F*L,G=G*M+k*L,M===1-Y){let w=1/Math.sqrt(X*X+K*K+U*U+G*G);X*=w,K*=w,U*=w,G*=w}}J[Q]=X,J[Q+1]=K,J[Q+2]=U,J[Q+3]=G}static multiplyQuaternionsFlat(J,Q,$,Z,W,H){let Y=$[Z],X=$[Z+1],K=$[Z+2],U=$[Z+3],G=W[H],q=W[H+1],E=W[H+2],F=W[H+3];return J[Q]=Y*F+U*G+X*E-K*q,J[Q+1]=X*F+U*q+K*G-Y*E,J[Q+2]=K*F+U*E+Y*q-X*G,J[Q+3]=U*F-Y*G-X*q-K*E,J}get x(){return this._x}set x(J){this._x=J,this._onChangeCallback()}get y(){return this._y}set y(J){this._y=J,this._onChangeCallback()}get z(){return this._z}set z(J){this._z=J,this._onChangeCallback()}get w(){return this._w}set w(J){this._w=J,this._onChangeCallback()}set(J,Q,$,Z){return this._x=J,this._y=Q,this._z=$,this._w=Z,this._onChangeCallback(),this}clone(){return new this.constructor(this._x,this._y,this._z,this._w)}copy(J){return this._x=J.x,this._y=J.y,this._z=J.z,this._w=J.w,this._onChangeCallback(),this}setFromEuler(J,Q=!0){let{_x:$,_y:Z,_z:W,_order:H}=J,Y=Math.cos,X=Math.sin,K=Y($/2),U=Y(Z/2),G=Y(W/2),q=X($/2),E=X(Z/2),F=X(W/2);switch(H){case"XYZ":this._x=q*U*G+K*E*F,this._y=K*E*G-q*U*F,this._z=K*U*F+q*E*G,this._w=K*U*G-q*E*F;break;case"YXZ":this._x=q*U*G+K*E*F,this._y=K*E*G-q*U*F,this._z=K*U*F-q*E*G,this._w=K*U*G+q*E*F;break;case"ZXY":this._x=q*U*G-K*E*F,this._y=K*E*G+q*U*F,this._z=K*U*F+q*E*G,this._w=K*U*G-q*E*F;break;case"ZYX":this._x=q*U*G-K*E*F,this._y=K*E*G+q*U*F,this._z=K*U*F-q*E*G,this._w=K*U*G+q*E*F;break;case"YZX":this._x=q*U*G+K*E*F,this._y=K*E*G+q*U*F,this._z=K*U*F-q*E*G,this._w=K*U*G-q*E*F;break;case"XZY":this._x=q*U*G-K*E*F,this._y=K*E*G-q*U*F,this._z=K*U*F+q*E*G,this._w=K*U*G+q*E*F;break;default:console.warn("THREE.Quaternion: .setFromEuler() encountered an unknown order: "+H)}if(Q===!0)this._onChangeCallback();return this}setFromAxisAngle(J,Q){let $=Q/2,Z=Math.sin($);return this._x=J.x*Z,this._y=J.y*Z,this._z=J.z*Z,this._w=Math.cos($),this._onChangeCallback(),this}setFromRotationMatrix(J){let Q=J.elements,$=Q[0],Z=Q[4],W=Q[8],H=Q[1],Y=Q[5],X=Q[9],K=Q[2],U=Q[6],G=Q[10],q=$+Y+G;if(q>0){let E=0.5/Math.sqrt(q+1);this._w=0.25/E,this._x=(U-X)*E,this._y=(W-K)*E,this._z=(H-Z)*E}else if($>Y&&$>G){let E=2*Math.sqrt(1+$-Y-G);this._w=(U-X)/E,this._x=0.25*E,this._y=(Z+H)/E,this._z=(W+K)/E}else if(Y>G){let E=2*Math.sqrt(1+Y-$-G);this._w=(W-K)/E,this._x=(Z+H)/E,this._y=0.25*E,this._z=(X+U)/E}else{let E=2*Math.sqrt(1+G-$-Y);this._w=(H-Z)/E,this._x=(W+K)/E,this._y=(X+U)/E,this._z=0.25*E}return this._onChangeCallback(),this}setFromUnitVectors(J,Q){let $=J.dot(Q)+1;if($<0.00000001)if($=0,Math.abs(J.x)>Math.abs(J.z))this._x=-J.y,this._y=J.x,this._z=0,this._w=$;else this._x=0,this._y=-J.z,this._z=J.y,this._w=$;else this._x=J.y*Q.z-J.z*Q.y,this._y=J.z*Q.x-J.x*Q.z,this._z=J.x*Q.y-J.y*Q.x,this._w=$;return this.normalize()}angleTo(J){return 2*Math.acos(Math.abs(xJ(this.dot(J),-1,1)))}rotateTowards(J,Q){let $=this.angleTo(J);if($===0)return this;let Z=Math.min(1,Q/$);return this.slerp(J,Z),this}identity(){return this.set(0,0,0,1)}invert(){return this.conjugate()}conjugate(){return this._x*=-1,this._y*=-1,this._z*=-1,this._onChangeCallback(),this}dot(J){return this._x*J._x+this._y*J._y+this._z*J._z+this._w*J._w}lengthSq(){return this._x*this._x+this._y*this._y+this._z*this._z+this._w*this._w}length(){return Math.sqrt(this._x*this._x+this._y*this._y+this._z*this._z+this._w*this._w)}normalize(){let J=this.length();if(J===0)this._x=0,this._y=0,this._z=0,this._w=1;else J=1/J,this._x=this._x*J,this._y=this._y*J,this._z=this._z*J,this._w=this._w*J;return this._onChangeCallback(),this}multiply(J){return this.multiplyQuaternions(this,J)}premultiply(J){return this.multiplyQuaternions(J,this)}multiplyQuaternions(J,Q){let{_x:$,_y:Z,_z:W,_w:H}=J,Y=Q._x,X=Q._y,K=Q._z,U=Q._w;return this._x=$*U+H*Y+Z*K-W*X,this._y=Z*U+H*X+W*Y-$*K,this._z=W*U+H*K+$*X-Z*Y,this._w=H*U-$*Y-Z*X-W*K,this._onChangeCallback(),this}slerp(J,Q){if(Q===0)return this;if(Q===1)return this.copy(J);let $=this._x,Z=this._y,W=this._z,H=this._w,Y=H*J._w+$*J._x+Z*J._y+W*J._z;if(Y<0)this._w=-J._w,this._x=-J._x,this._y=-J._y,this._z=-J._z,Y=-Y;else this.copy(J);if(Y>=1)return this._w=H,this._x=$,this._y=Z,this._z=W,this;let X=1-Y*Y;if(X<=Number.EPSILON){let E=1-Q;return this._w=E*H+Q*this._w,this._x=E*$+Q*this._x,this._y=E*Z+Q*this._y,this._z=E*W+Q*this._z,this.normalize(),this}let K=Math.sqrt(X),U=Math.atan2(K,Y),G=Math.sin((1-Q)*U)/K,q=Math.sin(Q*U)/K;return this._w=H*G+this._w*q,this._x=$*G+this._x*q,this._y=Z*G+this._y*q,this._z=W*G+this._z*q,this._onChangeCallback(),this}slerpQuaternions(J,Q,$){return this.copy(J).slerp(Q,$)}random(){let J=2*Math.PI*Math.random(),Q=2*Math.PI*Math.random(),$=Math.random(),Z=Math.sqrt(1-$),W=Math.sqrt($);return this.set(Z*Math.sin(J),Z*Math.cos(J),W*Math.sin(Q),W*Math.cos(Q))}equals(J){return J._x===this._x&&J._y===this._y&&J._z===this._z&&J._w===this._w}fromArray(J,Q=0){return this._x=J[Q],this._y=J[Q+1],this._z=J[Q+2],this._w=J[Q+3],this._onChangeCallback(),this}toArray(J=[],Q=0){return J[Q]=this._x,J[Q+1]=this._y,J[Q+2]=this._z,J[Q+3]=this._w,J}fromBufferAttribute(J,Q){return this._x=J.getX(Q),this._y=J.getY(Q),this._z=J.getZ(Q),this._w=J.getW(Q),this._onChangeCallback(),this}toJSON(){return this.toArray()}_onChange(J){return this._onChangeCallback=J,this}_onChangeCallback(){}*[Symbol.iterator](){yield this._x,yield this._y,yield this._z,yield this._w}}class A{constructor(J=0,Q=0,$=0){A.prototype.isVector3=!0,this.x=J,this.y=Q,this.z=$}set(J,Q,$){if($===void 0)$=this.z;return this.x=J,this.y=Q,this.z=$,this}setScalar(J){return this.x=J,this.y=J,this.z=J,this}setX(J){return this.x=J,this}setY(J){return this.y=J,this}setZ(J){return this.z=J,this}setComponent(J,Q){switch(J){case 0:this.x=Q;break;case 1:this.y=Q;break;case 2:this.z=Q;break;default:throw new Error("index is out of range: "+J)}return this}getComponent(J){switch(J){case 0:return this.x;case 1:return this.y;case 2:return this.z;default:throw new Error("index is out of range: "+J)}}clone(){return new this.constructor(this.x,this.y,this.z)}copy(J){return this.x=J.x,this.y=J.y,this.z=J.z,this}add(J){return this.x+=J.x,this.y+=J.y,this.z+=J.z,this}addScalar(J){return this.x+=J,this.y+=J,this.z+=J,this}addVectors(J,Q){return this.x=J.x+Q.x,this.y=J.y+Q.y,this.z=J.z+Q.z,this}addScaledVector(J,Q){return this.x+=J.x*Q,this.y+=J.y*Q,this.z+=J.z*Q,this}sub(J){return this.x-=J.x,this.y-=J.y,this.z-=J.z,this}subScalar(J){return this.x-=J,this.y-=J,this.z-=J,this}subVectors(J,Q){return this.x=J.x-Q.x,this.y=J.y-Q.y,this.z=J.z-Q.z,this}multiply(J){return this.x*=J.x,this.y*=J.y,this.z*=J.z,this}multiplyScalar(J){return this.x*=J,this.y*=J,this.z*=J,this}multiplyVectors(J,Q){return this.x=J.x*Q.x,this.y=J.y*Q.y,this.z=J.z*Q.z,this}applyEuler(J){return this.applyQuaternion(XZ.setFromEuler(J))}applyAxisAngle(J,Q){return this.applyQuaternion(XZ.setFromAxisAngle(J,Q))}applyMatrix3(J){let Q=this.x,$=this.y,Z=this.z,W=J.elements;return this.x=W[0]*Q+W[3]*$+W[6]*Z,this.y=W[1]*Q+W[4]*$+W[7]*Z,this.z=W[2]*Q+W[5]*$+W[8]*Z,this}applyNormalMatrix(J){return this.applyMatrix3(J).normalize()}applyMatrix4(J){let Q=this.x,$=this.y,Z=this.z,W=J.elements,H=1/(W[3]*Q+W[7]*$+W[11]*Z+W[15]);return this.x=(W[0]*Q+W[4]*$+W[8]*Z+W[12])*H,this.y=(W[1]*Q+W[5]*$+W[9]*Z+W[13])*H,this.z=(W[2]*Q+W[6]*$+W[10]*Z+W[14])*H,this}applyQuaternion(J){let Q=this.x,$=this.y,Z=this.z,W=J.x,H=J.y,Y=J.z,X=J.w,K=2*(H*Z-Y*$),U=2*(Y*Q-W*Z),G=2*(W*$-H*Q);return this.x=Q+X*K+H*G-Y*U,this.y=$+X*U+Y*K-W*G,this.z=Z+X*G+W*U-H*K,this}project(J){return this.applyMatrix4(J.matrixWorldInverse).applyMatrix4(J.projectionMatrix)}unproject(J){return this.applyMatrix4(J.projectionMatrixInverse).applyMatrix4(J.matrixWorld)}transformDirection(J){let Q=this.x,$=this.y,Z=this.z,W=J.elements;return this.x=W[0]*Q+W[4]*$+W[8]*Z,this.y=W[1]*Q+W[5]*$+W[9]*Z,this.z=W[2]*Q+W[6]*$+W[10]*Z,this.normalize()}divide(J){return this.x/=J.x,this.y/=J.y,this.z/=J.z,this}divideScalar(J){return this.multiplyScalar(1/J)}min(J){return this.x=Math.min(this.x,J.x),this.y=Math.min(this.y,J.y),this.z=Math.min(this.z,J.z),this}max(J){return this.x=Math.max(this.x,J.x),this.y=Math.max(this.y,J.y),this.z=Math.max(this.z,J.z),this}clamp(J,Q){return this.x=xJ(this.x,J.x,Q.x),this.y=xJ(this.y,J.y,Q.y),this.z=xJ(this.z,J.z,Q.z),this}clampScalar(J,Q){return this.x=xJ(this.x,J,Q),this.y=xJ(this.y,J,Q),this.z=xJ(this.z,J,Q),this}clampLength(J,Q){let $=this.length();return this.divideScalar($||1).multiplyScalar(xJ($,J,Q))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this.z=Math.floor(this.z),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this.z=Math.ceil(this.z),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this.z=Math.round(this.z),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this.z=Math.trunc(this.z),this}negate(){return this.x=-this.x,this.y=-this.y,this.z=-this.z,this}dot(J){return this.x*J.x+this.y*J.y+this.z*J.z}lengthSq(){return this.x*this.x+this.y*this.y+this.z*this.z}length(){return Math.sqrt(this.x*this.x+this.y*this.y+this.z*this.z)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)+Math.abs(this.z)}normalize(){return this.divideScalar(this.length()||1)}setLength(J){return this.normalize().multiplyScalar(J)}lerp(J,Q){return this.x+=(J.x-this.x)*Q,this.y+=(J.y-this.y)*Q,this.z+=(J.z-this.z)*Q,this}lerpVectors(J,Q,$){return this.x=J.x+(Q.x-J.x)*$,this.y=J.y+(Q.y-J.y)*$,this.z=J.z+(Q.z-J.z)*$,this}cross(J){return this.crossVectors(this,J)}crossVectors(J,Q){let{x:$,y:Z,z:W}=J,H=Q.x,Y=Q.y,X=Q.z;return this.x=Z*X-W*Y,this.y=W*H-$*X,this.z=$*Y-Z*H,this}projectOnVector(J){let Q=J.lengthSq();if(Q===0)return this.set(0,0,0);let $=J.dot(this)/Q;return this.copy(J).multiplyScalar($)}projectOnPlane(J){return a7.copy(this).projectOnVector(J),this.sub(a7)}reflect(J){return this.sub(a7.copy(J).multiplyScalar(2*this.dot(J)))}angleTo(J){let Q=Math.sqrt(this.lengthSq()*J.lengthSq());if(Q===0)return Math.PI/2;let $=this.dot(J)/Q;return Math.acos(xJ($,-1,1))}distanceTo(J){return Math.sqrt(this.distanceToSquared(J))}distanceToSquared(J){let Q=this.x-J.x,$=this.y-J.y,Z=this.z-J.z;return Q*Q+$*$+Z*Z}manhattanDistanceTo(J){return Math.abs(this.x-J.x)+Math.abs(this.y-J.y)+Math.abs(this.z-J.z)}setFromSpherical(J){return this.setFromSphericalCoords(J.radius,J.phi,J.theta)}setFromSphericalCoords(J,Q,$){let Z=Math.sin(Q)*J;return this.x=Z*Math.sin($),this.y=Math.cos(Q)*J,this.z=Z*Math.cos($),this}setFromCylindrical(J){return this.setFromCylindricalCoords(J.radius,J.theta,J.y)}setFromCylindricalCoords(J,Q,$){return this.x=J*Math.sin(Q),this.y=$,this.z=J*Math.cos(Q),this}setFromMatrixPosition(J){let Q=J.elements;return this.x=Q[12],this.y=Q[13],this.z=Q[14],this}setFromMatrixScale(J){let Q=this.setFromMatrixColumn(J,0).length(),$=this.setFromMatrixColumn(J,1).length(),Z=this.setFromMatrixColumn(J,2).length();return this.x=Q,this.y=$,this.z=Z,this}setFromMatrixColumn(J,Q){return this.fromArray(J.elements,Q*4)}setFromMatrix3Column(J,Q){return this.fromArray(J.elements,Q*3)}setFromEuler(J){return this.x=J._x,this.y=J._y,this.z=J._z,this}setFromColor(J){return this.x=J.r,this.y=J.g,this.z=J.b,this}equals(J){return J.x===this.x&&J.y===this.y&&J.z===this.z}fromArray(J,Q=0){return this.x=J[Q],this.y=J[Q+1],this.z=J[Q+2],this}toArray(J=[],Q=0){return J[Q]=this.x,J[Q+1]=this.y,J[Q+2]=this.z,J}fromBufferAttribute(J,Q){return this.x=J.getX(Q),this.y=J.getY(Q),this.z=J.getZ(Q),this}random(){return this.x=Math.random(),this.y=Math.random(),this.z=Math.random(),this}randomDirection(){let J=Math.random()*Math.PI*2,Q=Math.random()*2-1,$=Math.sqrt(1-Q*Q);return this.x=$*Math.cos(J),this.y=Q,this.z=$*Math.sin(J),this}*[Symbol.iterator](){yield this.x,yield this.y,yield this.z}}var a7=new A,XZ=new A0;class fJ{constructor(J,Q,$,Z,W,H,Y,X,K){if(fJ.prototype.isMatrix3=!0,this.elements=[1,0,0,0,1,0,0,0,1],J!==void 0)this.set(J,Q,$,Z,W,H,Y,X,K)}set(J,Q,$,Z,W,H,Y,X,K){let U=this.elements;return U[0]=J,U[1]=Z,U[2]=Y,U[3]=Q,U[4]=W,U[5]=X,U[6]=$,U[7]=H,U[8]=K,this}identity(){return this.set(1,0,0,0,1,0,0,0,1),this}copy(J){let Q=this.elements,$=J.elements;return Q[0]=$[0],Q[1]=$[1],Q[2]=$[2],Q[3]=$[3],Q[4]=$[4],Q[5]=$[5],Q[6]=$[6],Q[7]=$[7],Q[8]=$[8],this}extractBasis(J,Q,$){return J.setFromMatrix3Column(this,0),Q.setFromMatrix3Column(this,1),$.setFromMatrix3Column(this,2),this}setFromMatrix4(J){let Q=J.elements;return this.set(Q[0],Q[4],Q[8],Q[1],Q[5],Q[9],Q[2],Q[6],Q[10]),this}multiply(J){return this.multiplyMatrices(this,J)}premultiply(J){return this.multiplyMatrices(J,this)}multiplyMatrices(J,Q){let $=J.elements,Z=Q.elements,W=this.elements,H=$[0],Y=$[3],X=$[6],K=$[1],U=$[4],G=$[7],q=$[2],E=$[5],F=$[8],k=Z[0],M=Z[3],N=Z[6],O=Z[1],C=Z[4],L=Z[7],w=Z[2],v=Z[5],_=Z[8];return W[0]=H*k+Y*O+X*w,W[3]=H*M+Y*C+X*v,W[6]=H*N+Y*L+X*_,W[1]=K*k+U*O+G*w,W[4]=K*M+U*C+G*v,W[7]=K*N+U*L+G*_,W[2]=q*k+E*O+F*w,W[5]=q*M+E*C+F*v,W[8]=q*N+E*L+F*_,this}multiplyScalar(J){let Q=this.elements;return Q[0]*=J,Q[3]*=J,Q[6]*=J,Q[1]*=J,Q[4]*=J,Q[7]*=J,Q[2]*=J,Q[5]*=J,Q[8]*=J,this}determinant(){let J=this.elements,Q=J[0],$=J[1],Z=J[2],W=J[3],H=J[4],Y=J[5],X=J[6],K=J[7],U=J[8];return Q*H*U-Q*Y*K-$*W*U+$*Y*X+Z*W*K-Z*H*X}invert(){let J=this.elements,Q=J[0],$=J[1],Z=J[2],W=J[3],H=J[4],Y=J[5],X=J[6],K=J[7],U=J[8],G=U*H-Y*K,q=Y*X-U*W,E=K*W-H*X,F=Q*G+$*q+Z*E;if(F===0)return this.set(0,0,0,0,0,0,0,0,0);let k=1/F;return J[0]=G*k,J[1]=(Z*K-U*$)*k,J[2]=(Y*$-Z*H)*k,J[3]=q*k,J[4]=(U*Q-Z*X)*k,J[5]=(Z*W-Y*Q)*k,J[6]=E*k,J[7]=($*X-K*Q)*k,J[8]=(H*Q-$*W)*k,this}transpose(){let J,Q=this.elements;return J=Q[1],Q[1]=Q[3],Q[3]=J,J=Q[2],Q[2]=Q[6],Q[6]=J,J=Q[5],Q[5]=Q[7],Q[7]=J,this}getNormalMatrix(J){return this.setFromMatrix4(J).invert().transpose()}transposeIntoArray(J){let Q=this.elements;return J[0]=Q[0],J[1]=Q[3],J[2]=Q[6],J[3]=Q[1],J[4]=Q[4],J[5]=Q[7],J[6]=Q[2],J[7]=Q[5],J[8]=Q[8],this}setUvTransform(J,Q,$,Z,W,H,Y){let X=Math.cos(W),K=Math.sin(W);return this.set($*X,$*K,-$*(X*H+K*Y)+H+J,-Z*K,Z*X,-Z*(-K*H+X*Y)+Y+Q,0,0,1),this}scale(J,Q){return this.premultiply(r7.makeScale(J,Q)),this}rotate(J){return this.premultiply(r7.makeRotation(-J)),this}translate(J,Q){return this.premultiply(r7.makeTranslation(J,Q)),this}makeTranslation(J,Q){if(J.isVector2)this.set(1,0,J.x,0,1,J.y,0,0,1);else this.set(1,0,J,0,1,Q,0,0,1);return this}makeRotation(J){let Q=Math.cos(J),$=Math.sin(J);return this.set(Q,-$,0,$,Q,0,0,0,1),this}makeScale(J,Q){return this.set(J,0,0,0,Q,0,0,0,1),this}equals(J){let Q=this.elements,$=J.elements;for(let Z=0;Z<9;Z++)if(Q[Z]!==$[Z])return!1;return!0}fromArray(J,Q=0){for(let $=0;$<9;$++)this.elements[$]=J[$+Q];return this}toArray(J=[],Q=0){let $=this.elements;return J[Q]=$[0],J[Q+1]=$[1],J[Q+2]=$[2],J[Q+3]=$[3],J[Q+4]=$[4],J[Q+5]=$[5],J[Q+6]=$[6],J[Q+7]=$[7],J[Q+8]=$[8],J}clone(){return new this.constructor().fromArray(this.elements)}}var r7=new fJ;function O$(J){for(let Q=J.length-1;Q>=0;--Q)if(J[Q]>=65535)return!0;return!1}function A9(J){return document.createElementNS("http://www.w3.org/1999/xhtml",J)}function pW(){let J=A9("canvas");return J.style.display="block",J}var KZ={};function $9(J){if(J in KZ)return;KZ[J]=!0,console.warn(J)}function lW(J,Q,$){return new Promise(function(Z,W){function H(){switch(J.clientWaitSync(Q,J.SYNC_FLUSH_COMMANDS_BIT,0)){case J.WAIT_FAILED:W();break;case J.TIMEOUT_EXPIRED:setTimeout(H,$);break;default:Z()}}setTimeout(H,$)})}var UZ=new fJ().set(0.4123908,0.3575843,0.1804808,0.212639,0.7151687,0.0721923,0.0193308,0.1191948,0.9505322),GZ=new fJ().set(3.2409699,-1.5373832,-0.4986108,-0.9692436,1.8759675,0.0415551,0.0556301,-0.203977,1.0569715);function jY(){let J={enabled:!0,workingColorSpace:"srgb-linear",spaces:{},convert:function(W,H,Y){if(this.enabled===!1||H===Y||!H||!Y)return W;if(this.spaces[H].transfer==="srgb")W.r=D8(W.r),W.g=D8(W.g),W.b=D8(W.b);if(this.spaces[H].primaries!==this.spaces[Y].primaries)W.applyMatrix3(this.spaces[H].toXYZ),W.applyMatrix3(this.spaces[Y].fromXYZ);if(this.spaces[Y].transfer==="srgb")W.r=T9(W.r),W.g=T9(W.g),W.b=T9(W.b);return W},workingToColorSpace:function(W,H){return this.convert(W,this.workingColorSpace,H)},colorSpaceToWorking:function(W,H){return this.convert(W,H,this.workingColorSpace)},getPrimaries:function(W){return this.spaces[W].primaries},getTransfer:function(W){if(W==="")return"linear";return this.spaces[W].transfer},getLuminanceCoefficients:function(W,H=this.workingColorSpace){return W.fromArray(this.spaces[H].luminanceCoefficients)},define:function(W){Object.assign(this.spaces,W)},_getMatrix:function(W,H,Y){return W.copy(this.spaces[H].toXYZ).multiply(this.spaces[Y].fromXYZ)},_getDrawingBufferColorSpace:function(W){return this.spaces[W].outputColorSpaceConfig.drawingBufferColorSpace},_getUnpackColorSpace:function(W=this.workingColorSpace){return this.spaces[W].workingColorSpaceConfig.unpackColorSpace},fromWorkingColorSpace:function(W,H){return $9("THREE.ColorManagement: .fromWorkingColorSpace() has been renamed to .workingToColorSpace()."),J.workingToColorSpace(W,H)},toWorkingColorSpace:function(W,H){return $9("THREE.ColorManagement: .toWorkingColorSpace() has been renamed to .colorSpaceToWorking()."),J.colorSpaceToWorking(W,H)}},Q=[0.64,0.33,0.3,0.6,0.15,0.06],$=[0.2126,0.7152,0.0722],Z=[0.3127,0.329];return J.define({["srgb-linear"]:{primaries:Q,whitePoint:Z,transfer:"linear",toXYZ:UZ,fromXYZ:GZ,luminanceCoefficients:$,workingColorSpaceConfig:{unpackColorSpace:"srgb"},outputColorSpaceConfig:{drawingBufferColorSpace:"srgb"}},["srgb"]:{primaries:Q,whitePoint:Z,transfer:"srgb",toXYZ:UZ,fromXYZ:GZ,luminanceCoefficients:$,outputColorSpaceConfig:{drawingBufferColorSpace:"srgb"}}}),J}var lJ=jY();function D8(J){return J<0.04045?J*0.0773993808:Math.pow(J*0.9478672986+0.0521327014,2.4)}function T9(J){return J<0.0031308?J*12.92:1.055*Math.pow(J,0.41666)-0.055}var F9;class F${static getDataURL(J,Q="image/png"){if(/^data:/i.test(J.src))return J.src;if(typeof HTMLCanvasElement==="undefined")return J.src;let $;if(J instanceof HTMLCanvasElement)$=J;else{if(F9===void 0)F9=A9("canvas");F9.width=J.width,F9.height=J.height;let Z=F9.getContext("2d");if(J instanceof ImageData)Z.putImageData(J,0,0);else Z.drawImage(J,0,0,J.width,J.height);$=F9}return $.toDataURL(Q)}static sRGBToLinear(J){if(typeof HTMLImageElement!=="undefined"&&J instanceof HTMLImageElement||typeof HTMLCanvasElement!=="undefined"&&J instanceof HTMLCanvasElement||typeof ImageBitmap!=="undefined"&&J instanceof ImageBitmap){let Q=A9("canvas");Q.width=J.width,Q.height=J.height;let $=Q.getContext("2d");$.drawImage(J,0,0,J.width,J.height);let Z=$.getImageData(0,0,J.width,J.height),W=Z.data;for(let H=0;H<W.length;H++)W[H]=D8(W[H]/255)*255;return $.putImageData(Z,0,0),Q}else if(J.data){let Q=J.data.slice(0);for(let $=0;$<Q.length;$++)if(Q instanceof Uint8Array||Q instanceof Uint8ClampedArray)Q[$]=Math.floor(D8(Q[$]/255)*255);else Q[$]=D8(Q[$]);return{data:Q,width:J.width,height:J.height}}else return console.warn("THREE.ImageUtils.sRGBToLinear(): Unsupported image type. No color space conversion applied."),J}}var yY=0;class N6{constructor(J=null){this.isSource=!0,Object.defineProperty(this,"id",{value:yY++}),this.uuid=Q8(),this.data=J,this.dataReady=!0,this.version=0}getSize(J){let Q=this.data;if(Q instanceof HTMLVideoElement)J.set(Q.videoWidth,Q.videoHeight,0);else if(Q instanceof VideoFrame)J.set(Q.displayHeight,Q.displayWidth,0);else if(Q!==null)J.set(Q.width,Q.height,Q.depth||0);else J.set(0,0,0);return J}set needsUpdate(J){if(J===!0)this.version++}toJSON(J){let Q=J===void 0||typeof J==="string";if(!Q&&J.images[this.uuid]!==void 0)return J.images[this.uuid];let $={uuid:this.uuid,url:""},Z=this.data;if(Z!==null){let W;if(Array.isArray(Z)){W=[];for(let H=0,Y=Z.length;H<Y;H++)if(Z[H].isDataTexture)W.push(t7(Z[H].image));else W.push(t7(Z[H]))}else W=t7(Z);$.url=W}if(!Q)J.images[this.uuid]=$;return $}}function t7(J){if(typeof HTMLImageElement!=="undefined"&&J instanceof HTMLImageElement||typeof HTMLCanvasElement!=="undefined"&&J instanceof HTMLCanvasElement||typeof ImageBitmap!=="undefined"&&J instanceof ImageBitmap)return F$.getDataURL(J);else if(J.data)return{data:Array.from(J.data),width:J.width,height:J.height,type:J.data.constructor.name};else return console.warn("THREE.Texture: Unable to serialize Texture."),{}}var vY=0,e7=new A;class E0 extends w8{constructor(J=E0.DEFAULT_IMAGE,Q=E0.DEFAULT_MAPPING,$=1001,Z=1001,W=1006,H=1008,Y=1023,X=1009,K=E0.DEFAULT_ANISOTROPY,U=""){super();this.isTexture=!0,Object.defineProperty(this,"id",{value:vY++}),this.uuid=Q8(),this.name="",this.source=new N6(J),this.mipmaps=[],this.mapping=Q,this.channel=0,this.wrapS=$,this.wrapT=Z,this.magFilter=W,this.minFilter=H,this.anisotropy=K,this.format=Y,this.internalFormat=null,this.type=X,this.offset=new PJ(0,0),this.repeat=new PJ(1,1),this.center=new PJ(0,0),this.rotation=0,this.matrixAutoUpdate=!0,this.matrix=new fJ,this.generateMipmaps=!0,this.premultiplyAlpha=!1,this.flipY=!0,this.unpackAlignment=4,this.colorSpace=U,this.userData={},this.updateRanges=[],this.version=0,this.onUpdate=null,this.renderTarget=null,this.isRenderTargetTexture=!1,this.isArrayTexture=J&&J.depth&&J.depth>1?!0:!1,this.pmremVersion=0}get width(){return this.source.getSize(e7).x}get height(){return this.source.getSize(e7).y}get depth(){return this.source.getSize(e7).z}get image(){return this.source.data}set image(J=null){this.source.data=J}updateMatrix(){this.matrix.setUvTransform(this.offset.x,this.offset.y,this.repeat.x,this.repeat.y,this.rotation,this.center.x,this.center.y)}addUpdateRange(J,Q){this.updateRanges.push({start:J,count:Q})}clearUpdateRanges(){this.updateRanges.length=0}clone(){return new this.constructor().copy(this)}copy(J){return this.name=J.name,this.source=J.source,this.mipmaps=J.mipmaps.slice(0),this.mapping=J.mapping,this.channel=J.channel,this.wrapS=J.wrapS,this.wrapT=J.wrapT,this.magFilter=J.magFilter,this.minFilter=J.minFilter,this.anisotropy=J.anisotropy,this.format=J.format,this.internalFormat=J.internalFormat,this.type=J.type,this.offset.copy(J.offset),this.repeat.copy(J.repeat),this.center.copy(J.center),this.rotation=J.rotation,this.matrixAutoUpdate=J.matrixAutoUpdate,this.matrix.copy(J.matrix),this.generateMipmaps=J.generateMipmaps,this.premultiplyAlpha=J.premultiplyAlpha,this.flipY=J.flipY,this.unpackAlignment=J.unpackAlignment,this.colorSpace=J.colorSpace,this.renderTarget=J.renderTarget,this.isRenderTargetTexture=J.isRenderTargetTexture,this.isArrayTexture=J.isArrayTexture,this.userData=JSON.parse(JSON.stringify(J.userData)),this.needsUpdate=!0,this}setValues(J){for(let Q in J){let $=J[Q];if($===void 0){console.warn(`THREE.Texture.setValues(): parameter '${Q}' has value of undefined.`);continue}let Z=this[Q];if(Z===void 0){console.warn(`THREE.Texture.setValues(): property '${Q}' does not exist.`);continue}if(Z&&$&&(Z.isVector2&&$.isVector2))Z.copy($);else if(Z&&$&&(Z.isVector3&&$.isVector3))Z.copy($);else if(Z&&$&&(Z.isMatrix3&&$.isMatrix3))Z.copy($);else this[Q]=$}}toJSON(J){let Q=J===void 0||typeof J==="string";if(!Q&&J.textures[this.uuid]!==void 0)return J.textures[this.uuid];let $={metadata:{version:4.7,type:"Texture",generator:"Texture.toJSON"},uuid:this.uuid,name:this.name,image:this.source.toJSON(J).uuid,mapping:this.mapping,channel:this.channel,repeat:[this.repeat.x,this.repeat.y],offset:[this.offset.x,this.offset.y],center:[this.center.x,this.center.y],rotation:this.rotation,wrap:[this.wrapS,this.wrapT],format:this.format,internalFormat:this.internalFormat,type:this.type,colorSpace:this.colorSpace,minFilter:this.minFilter,magFilter:this.magFilter,anisotropy:this.anisotropy,flipY:this.flipY,generateMipmaps:this.generateMipmaps,premultiplyAlpha:this.premultiplyAlpha,unpackAlignment:this.unpackAlignment};if(Object.keys(this.userData).length>0)$.userData=this.userData;if(!Q)J.textures[this.uuid]=$;return $}dispose(){this.dispatchEvent({type:"dispose"})}transformUv(J){if(this.mapping!==300)return J;if(J.applyMatrix3(this.matrix),J.x<0||J.x>1)switch(this.wrapS){case 1000:J.x=J.x-Math.floor(J.x);break;case 1001:J.x=J.x<0?0:1;break;case 1002:if(Math.abs(Math.floor(J.x)%2)===1)J.x=Math.ceil(J.x)-J.x;else J.x=J.x-Math.floor(J.x);break}if(J.y<0||J.y>1)switch(this.wrapT){case 1000:J.y=J.y-Math.floor(J.y);break;case 1001:J.y=J.y<0?0:1;break;case 1002:if(Math.abs(Math.floor(J.y)%2)===1)J.y=Math.ceil(J.y)-J.y;else J.y=J.y-Math.floor(J.y);break}if(this.flipY)J.y=1-J.y;return J}set needsUpdate(J){if(J===!0)this.version++,this.source.needsUpdate=!0}set needsPMREMUpdate(J){if(J===!0)this.pmremVersion++}}E0.DEFAULT_IMAGE=null;E0.DEFAULT_MAPPING=300;E0.DEFAULT_ANISOTROPY=1;class sJ{constructor(J=0,Q=0,$=0,Z=1){sJ.prototype.isVector4=!0,this.x=J,this.y=Q,this.z=$,this.w=Z}get width(){return this.z}set width(J){this.z=J}get height(){return this.w}set height(J){this.w=J}set(J,Q,$,Z){return this.x=J,this.y=Q,this.z=$,this.w=Z,this}setScalar(J){return this.x=J,this.y=J,this.z=J,this.w=J,this}setX(J){return this.x=J,this}setY(J){return this.y=J,this}setZ(J){return this.z=J,this}setW(J){return this.w=J,this}setComponent(J,Q){switch(J){case 0:this.x=Q;break;case 1:this.y=Q;break;case 2:this.z=Q;break;case 3:this.w=Q;break;default:throw new Error("index is out of range: "+J)}return this}getComponent(J){switch(J){case 0:return this.x;case 1:return this.y;case 2:return this.z;case 3:return this.w;default:throw new Error("index is out of range: "+J)}}clone(){return new this.constructor(this.x,this.y,this.z,this.w)}copy(J){return this.x=J.x,this.y=J.y,this.z=J.z,this.w=J.w!==void 0?J.w:1,this}add(J){return this.x+=J.x,this.y+=J.y,this.z+=J.z,this.w+=J.w,this}addScalar(J){return this.x+=J,this.y+=J,this.z+=J,this.w+=J,this}addVectors(J,Q){return this.x=J.x+Q.x,this.y=J.y+Q.y,this.z=J.z+Q.z,this.w=J.w+Q.w,this}addScaledVector(J,Q){return this.x+=J.x*Q,this.y+=J.y*Q,this.z+=J.z*Q,this.w+=J.w*Q,this}sub(J){return this.x-=J.x,this.y-=J.y,this.z-=J.z,this.w-=J.w,this}subScalar(J){return this.x-=J,this.y-=J,this.z-=J,this.w-=J,this}subVectors(J,Q){return this.x=J.x-Q.x,this.y=J.y-Q.y,this.z=J.z-Q.z,this.w=J.w-Q.w,this}multiply(J){return this.x*=J.x,this.y*=J.y,this.z*=J.z,this.w*=J.w,this}multiplyScalar(J){return this.x*=J,this.y*=J,this.z*=J,this.w*=J,this}applyMatrix4(J){let Q=this.x,$=this.y,Z=this.z,W=this.w,H=J.elements;return this.x=H[0]*Q+H[4]*$+H[8]*Z+H[12]*W,this.y=H[1]*Q+H[5]*$+H[9]*Z+H[13]*W,this.z=H[2]*Q+H[6]*$+H[10]*Z+H[14]*W,this.w=H[3]*Q+H[7]*$+H[11]*Z+H[15]*W,this}divide(J){return this.x/=J.x,this.y/=J.y,this.z/=J.z,this.w/=J.w,this}divideScalar(J){return this.multiplyScalar(1/J)}setAxisAngleFromQuaternion(J){this.w=2*Math.acos(J.w);let Q=Math.sqrt(1-J.w*J.w);if(Q<0.0001)this.x=1,this.y=0,this.z=0;else this.x=J.x/Q,this.y=J.y/Q,this.z=J.z/Q;return this}setAxisAngleFromRotationMatrix(J){let Q,$,Z,W,H=0.01,Y=0.1,X=J.elements,K=X[0],U=X[4],G=X[8],q=X[1],E=X[5],F=X[9],k=X[2],M=X[6],N=X[10];if(Math.abs(U-q)<0.01&&Math.abs(G-k)<0.01&&Math.abs(F-M)<0.01){if(Math.abs(U+q)<0.1&&Math.abs(G+k)<0.1&&Math.abs(F+M)<0.1&&Math.abs(K+E+N-3)<0.1)return this.set(1,0,0,0),this;Q=Math.PI;let C=(K+1)/2,L=(E+1)/2,w=(N+1)/2,v=(U+q)/4,_=(G+k)/4,T=(F+M)/4;if(C>L&&C>w)if(C<0.01)$=0,Z=0.707106781,W=0.707106781;else $=Math.sqrt(C),Z=v/$,W=_/$;else if(L>w)if(L<0.01)$=0.707106781,Z=0,W=0.707106781;else Z=Math.sqrt(L),$=v/Z,W=T/Z;else if(w<0.01)$=0.707106781,Z=0.707106781,W=0;else W=Math.sqrt(w),$=_/W,Z=T/W;return this.set($,Z,W,Q),this}let O=Math.sqrt((M-F)*(M-F)+(G-k)*(G-k)+(q-U)*(q-U));if(Math.abs(O)<0.001)O=1;return this.x=(M-F)/O,this.y=(G-k)/O,this.z=(q-U)/O,this.w=Math.acos((K+E+N-1)/2),this}setFromMatrixPosition(J){let Q=J.elements;return this.x=Q[12],this.y=Q[13],this.z=Q[14],this.w=Q[15],this}min(J){return this.x=Math.min(this.x,J.x),this.y=Math.min(this.y,J.y),this.z=Math.min(this.z,J.z),this.w=Math.min(this.w,J.w),this}max(J){return this.x=Math.max(this.x,J.x),this.y=Math.max(this.y,J.y),this.z=Math.max(this.z,J.z),this.w=Math.max(this.w,J.w),this}clamp(J,Q){return this.x=xJ(this.x,J.x,Q.x),this.y=xJ(this.y,J.y,Q.y),this.z=xJ(this.z,J.z,Q.z),this.w=xJ(this.w,J.w,Q.w),this}clampScalar(J,Q){return this.x=xJ(this.x,J,Q),this.y=xJ(this.y,J,Q),this.z=xJ(this.z,J,Q),this.w=xJ(this.w,J,Q),this}clampLength(J,Q){let $=this.length();return this.divideScalar($||1).multiplyScalar(xJ($,J,Q))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this.z=Math.floor(this.z),this.w=Math.floor(this.w),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this.z=Math.ceil(this.z),this.w=Math.ceil(this.w),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this.z=Math.round(this.z),this.w=Math.round(this.w),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this.z=Math.trunc(this.z),this.w=Math.trunc(this.w),this}negate(){return this.x=-this.x,this.y=-this.y,this.z=-this.z,this.w=-this.w,this}dot(J){return this.x*J.x+this.y*J.y+this.z*J.z+this.w*J.w}lengthSq(){return this.x*this.x+this.y*this.y+this.z*this.z+this.w*this.w}length(){return Math.sqrt(this.x*this.x+this.y*this.y+this.z*this.z+this.w*this.w)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)+Math.abs(this.z)+Math.abs(this.w)}normalize(){return this.divideScalar(this.length()||1)}setLength(J){return this.normalize().multiplyScalar(J)}lerp(J,Q){return this.x+=(J.x-this.x)*Q,this.y+=(J.y-this.y)*Q,this.z+=(J.z-this.z)*Q,this.w+=(J.w-this.w)*Q,this}lerpVectors(J,Q,$){return this.x=J.x+(Q.x-J.x)*$,this.y=J.y+(Q.y-J.y)*$,this.z=J.z+(Q.z-J.z)*$,this.w=J.w+(Q.w-J.w)*$,this}equals(J){return J.x===this.x&&J.y===this.y&&J.z===this.z&&J.w===this.w}fromArray(J,Q=0){return this.x=J[Q],this.y=J[Q+1],this.z=J[Q+2],this.w=J[Q+3],this}toArray(J=[],Q=0){return J[Q]=this.x,J[Q+1]=this.y,J[Q+2]=this.z,J[Q+3]=this.w,J}fromBufferAttribute(J,Q){return this.x=J.getX(Q),this.y=J.getY(Q),this.z=J.getZ(Q),this.w=J.getW(Q),this}random(){return this.x=Math.random(),this.y=Math.random(),this.z=Math.random(),this.w=Math.random(),this}*[Symbol.iterator](){yield this.x,yield this.y,yield this.z,yield this.w}}class R$ extends w8{constructor(J=1,Q=1,$={}){super();$=Object.assign({generateMipmaps:!1,internalFormat:null,minFilter:1006,depthBuffer:!0,stencilBuffer:!1,resolveDepthBuffer:!0,resolveStencilBuffer:!0,depthTexture:null,samples:0,count:1,depth:1,multiview:!1},$),this.isRenderTarget=!0,this.width=J,this.height=Q,this.depth=$.depth,this.scissor=new sJ(0,0,J,Q),this.scissorTest=!1,this.viewport=new sJ(0,0,J,Q);let Z={width:J,height:Q,depth:$.depth},W=new E0(Z);this.textures=[];let H=$.count;for(let Y=0;Y<H;Y++)this.textures[Y]=W.clone(),this.textures[Y].isRenderTargetTexture=!0,this.textures[Y].renderTarget=this;this._setTextureOptions($),this.depthBuffer=$.depthBuffer,this.stencilBuffer=$.stencilBuffer,this.resolveDepthBuffer=$.resolveDepthBuffer,this.resolveStencilBuffer=$.resolveStencilBuffer,this._depthTexture=null,this.depthTexture=$.depthTexture,this.samples=$.samples,this.multiview=$.multiview}_setTextureOptions(J={}){let Q={minFilter:1006,generateMipmaps:!1,flipY:!1,internalFormat:null};if(J.mapping!==void 0)Q.mapping=J.mapping;if(J.wrapS!==void 0)Q.wrapS=J.wrapS;if(J.wrapT!==void 0)Q.wrapT=J.wrapT;if(J.wrapR!==void 0)Q.wrapR=J.wrapR;if(J.magFilter!==void 0)Q.magFilter=J.magFilter;if(J.minFilter!==void 0)Q.minFilter=J.minFilter;if(J.format!==void 0)Q.format=J.format;if(J.type!==void 0)Q.type=J.type;if(J.anisotropy!==void 0)Q.anisotropy=J.anisotropy;if(J.colorSpace!==void 0)Q.colorSpace=J.colorSpace;if(J.flipY!==void 0)Q.flipY=J.flipY;if(J.generateMipmaps!==void 0)Q.generateMipmaps=J.generateMipmaps;if(J.internalFormat!==void 0)Q.internalFormat=J.internalFormat;for(let $=0;$<this.textures.length;$++)this.textures[$].setValues(Q)}get texture(){return this.textures[0]}set texture(J){this.textures[0]=J}set depthTexture(J){if(this._depthTexture!==null)this._depthTexture.renderTarget=null;if(J!==null)J.renderTarget=this;this._depthTexture=J}get depthTexture(){return this._depthTexture}setSize(J,Q,$=1){if(this.width!==J||this.height!==Q||this.depth!==$){this.width=J,this.height=Q,this.depth=$;for(let Z=0,W=this.textures.length;Z<W;Z++)this.textures[Z].image.width=J,this.textures[Z].image.height=Q,this.textures[Z].image.depth=$,this.textures[Z].isArrayTexture=this.textures[Z].image.depth>1;this.dispose()}this.viewport.set(0,0,J,Q),this.scissor.set(0,0,J,Q)}clone(){return new this.constructor().copy(this)}copy(J){this.width=J.width,this.height=J.height,this.depth=J.depth,this.scissor.copy(J.scissor),this.scissorTest=J.scissorTest,this.viewport.copy(J.viewport),this.textures.length=0;for(let Q=0,$=J.textures.length;Q<$;Q++){this.textures[Q]=J.textures[Q].clone(),this.textures[Q].isRenderTargetTexture=!0,this.textures[Q].renderTarget=this;let Z=Object.assign({},J.textures[Q].image);this.textures[Q].source=new N6(Z)}if(this.depthBuffer=J.depthBuffer,this.stencilBuffer=J.stencilBuffer,this.resolveDepthBuffer=J.resolveDepthBuffer,this.resolveStencilBuffer=J.resolveStencilBuffer,J.depthTexture!==null)this.depthTexture=J.depthTexture.clone();return this.samples=J.samples,this}dispose(){this.dispatchEvent({type:"dispose"})}}class _8 extends R${constructor(J=1,Q=1,$={}){super(J,Q,$);this.isWebGLRenderTarget=!0}}class L7 extends E0{constructor(J=null,Q=1,$=1,Z=1){super(null);this.isDataArrayTexture=!0,this.image={data:J,width:Q,height:$,depth:Z},this.magFilter=1003,this.minFilter=1003,this.wrapR=1001,this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1,this.layerUpdates=new Set}addLayerUpdate(J){this.layerUpdates.add(J)}clearLayerUpdates(){this.layerUpdates.clear()}}class k$ extends E0{constructor(J=null,Q=1,$=1,Z=1){super(null);this.isData3DTexture=!0,this.image={data:J,width:Q,height:$,depth:Z},this.magFilter=1003,this.minFilter=1003,this.wrapR=1001,this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1}}class S0{constructor(J=new A(1/0,1/0,1/0),Q=new A(-1/0,-1/0,-1/0)){this.isBox3=!0,this.min=J,this.max=Q}set(J,Q){return this.min.copy(J),this.max.copy(Q),this}setFromArray(J){this.makeEmpty();for(let Q=0,$=J.length;Q<$;Q+=3)this.expandByPoint(a0.fromArray(J,Q));return this}setFromBufferAttribute(J){this.makeEmpty();for(let Q=0,$=J.count;Q<$;Q++)this.expandByPoint(a0.fromBufferAttribute(J,Q));return this}setFromPoints(J){this.makeEmpty();for(let Q=0,$=J.length;Q<$;Q++)this.expandByPoint(J[Q]);return this}setFromCenterAndSize(J,Q){let $=a0.copy(Q).multiplyScalar(0.5);return this.min.copy(J).sub($),this.max.copy(J).add($),this}setFromObject(J,Q=!1){return this.makeEmpty(),this.expandByObject(J,Q)}clone(){return new this.constructor().copy(this)}copy(J){return this.min.copy(J.min),this.max.copy(J.max),this}makeEmpty(){return this.min.x=this.min.y=this.min.z=1/0,this.max.x=this.max.y=this.max.z=-1/0,this}isEmpty(){return this.max.x<this.min.x||this.max.y<this.min.y||this.max.z<this.min.z}getCenter(J){return this.isEmpty()?J.set(0,0,0):J.addVectors(this.min,this.max).multiplyScalar(0.5)}getSize(J){return this.isEmpty()?J.set(0,0,0):J.subVectors(this.max,this.min)}expandByPoint(J){return this.min.min(J),this.max.max(J),this}expandByVector(J){return this.min.sub(J),this.max.add(J),this}expandByScalar(J){return this.min.addScalar(-J),this.max.addScalar(J),this}expandByObject(J,Q=!1){J.updateWorldMatrix(!1,!1);let $=J.geometry;if($!==void 0){let W=$.getAttribute("position");if(Q===!0&&W!==void 0&&J.isInstancedMesh!==!0)for(let H=0,Y=W.count;H<Y;H++){if(J.isMesh===!0)J.getVertexPosition(H,a0);else a0.fromBufferAttribute(W,H);a0.applyMatrix4(J.matrixWorld),this.expandByPoint(a0)}else{if(J.boundingBox!==void 0){if(J.boundingBox===null)J.computeBoundingBox();T6.copy(J.boundingBox)}else{if($.boundingBox===null)$.computeBoundingBox();T6.copy($.boundingBox)}T6.applyMatrix4(J.matrixWorld),this.union(T6)}}let Z=J.children;for(let W=0,H=Z.length;W<H;W++)this.expandByObject(Z[W],Q);return this}containsPoint(J){return J.x>=this.min.x&&J.x<=this.max.x&&J.y>=this.min.y&&J.y<=this.max.y&&J.z>=this.min.z&&J.z<=this.max.z}containsBox(J){return this.min.x<=J.min.x&&J.max.x<=this.max.x&&this.min.y<=J.min.y&&J.max.y<=this.max.y&&this.min.z<=J.min.z&&J.max.z<=this.max.z}getParameter(J,Q){return Q.set((J.x-this.min.x)/(this.max.x-this.min.x),(J.y-this.min.y)/(this.max.y-this.min.y),(J.z-this.min.z)/(this.max.z-this.min.z))}intersectsBox(J){return J.max.x>=this.min.x&&J.min.x<=this.max.x&&J.max.y>=this.min.y&&J.min.y<=this.max.y&&J.max.z>=this.min.z&&J.min.z<=this.max.z}intersectsSphere(J){return this.clampPoint(J.center,a0),a0.distanceToSquared(J.center)<=J.radius*J.radius}intersectsPlane(J){let Q,$;if(J.normal.x>0)Q=J.normal.x*this.min.x,$=J.normal.x*this.max.x;else Q=J.normal.x*this.max.x,$=J.normal.x*this.min.x;if(J.normal.y>0)Q+=J.normal.y*this.min.y,$+=J.normal.y*this.max.y;else Q+=J.normal.y*this.max.y,$+=J.normal.y*this.min.y;if(J.normal.z>0)Q+=J.normal.z*this.min.z,$+=J.normal.z*this.max.z;else Q+=J.normal.z*this.max.z,$+=J.normal.z*this.min.z;return Q<=-J.constant&&$>=-J.constant}intersectsTriangle(J){if(this.isEmpty())return!1;this.getCenter(a9),A6.subVectors(this.max,a9),R9.subVectors(J.a,a9),k9.subVectors(J.b,a9),M9.subVectors(J.c,a9),A8.subVectors(k9,R9),S8.subVectors(M9,k9),r8.subVectors(R9,M9);let Q=[0,-A8.z,A8.y,0,-S8.z,S8.y,0,-r8.z,r8.y,A8.z,0,-A8.x,S8.z,0,-S8.x,r8.z,0,-r8.x,-A8.y,A8.x,0,-S8.y,S8.x,0,-r8.y,r8.x,0];if(!JQ(Q,R9,k9,M9,A6))return!1;if(Q=[1,0,0,0,1,0,0,0,1],!JQ(Q,R9,k9,M9,A6))return!1;return S6.crossVectors(A8,S8),Q=[S6.x,S6.y,S6.z],JQ(Q,R9,k9,M9,A6)}clampPoint(J,Q){return Q.copy(J).clamp(this.min,this.max)}distanceToPoint(J){return this.clampPoint(J,a0).distanceTo(J)}getBoundingSphere(J){if(this.isEmpty())J.makeEmpty();else this.getCenter(J.center),J.radius=this.getSize(a0).length()*0.5;return J}intersect(J){if(this.min.max(J.min),this.max.min(J.max),this.isEmpty())this.makeEmpty();return this}union(J){return this.min.min(J.min),this.max.max(J.max),this}applyMatrix4(J){if(this.isEmpty())return this;return N8[0].set(this.min.x,this.min.y,this.min.z).applyMatrix4(J),N8[1].set(this.min.x,this.min.y,this.max.z).applyMatrix4(J),N8[2].set(this.min.x,this.max.y,this.min.z).applyMatrix4(J),N8[3].set(this.min.x,this.max.y,this.max.z).applyMatrix4(J),N8[4].set(this.max.x,this.min.y,this.min.z).applyMatrix4(J),N8[5].set(this.max.x,this.min.y,this.max.z).applyMatrix4(J),N8[6].set(this.max.x,this.max.y,this.min.z).applyMatrix4(J),N8[7].set(this.max.x,this.max.y,this.max.z).applyMatrix4(J),this.setFromPoints(N8),this}translate(J){return this.min.add(J),this.max.add(J),this}equals(J){return J.min.equals(this.min)&&J.max.equals(this.max)}toJSON(){return{min:this.min.toArray(),max:this.max.toArray()}}fromJSON(J){return this.min.fromArray(J.min),this.max.fromArray(J.max),this}}var N8=[new A,new A,new A,new A,new A,new A,new A,new A],a0=new A,T6=new S0,R9=new A,k9=new A,M9=new A,A8=new A,S8=new A,r8=new A,a9=new A,A6=new A,S6=new A,t8=new A;function JQ(J,Q,$,Z,W){for(let H=0,Y=J.length-3;H<=Y;H+=3){t8.fromArray(J,H);let X=W.x*Math.abs(t8.x)+W.y*Math.abs(t8.y)+W.z*Math.abs(t8.z),K=Q.dot(t8),U=$.dot(t8),G=Z.dot(t8);if(Math.max(-Math.max(K,U,G),Math.min(K,U,G))>X)return!1}return!0}var fY=new S0,r9=new A,QQ=new A;class x0{constructor(J=new A,Q=-1){this.isSphere=!0,this.center=J,this.radius=Q}set(J,Q){return this.center.copy(J),this.radius=Q,this}setFromPoints(J,Q){let $=this.center;if(Q!==void 0)$.copy(Q);else fY.setFromPoints(J).getCenter($);let Z=0;for(let W=0,H=J.length;W<H;W++)Z=Math.max(Z,$.distanceToSquared(J[W]));return this.radius=Math.sqrt(Z),this}copy(J){return this.center.copy(J.center),this.radius=J.radius,this}isEmpty(){return this.radius<0}makeEmpty(){return this.center.set(0,0,0),this.radius=-1,this}containsPoint(J){return J.distanceToSquared(this.center)<=this.radius*this.radius}distanceToPoint(J){return J.distanceTo(this.center)-this.radius}intersectsSphere(J){let Q=this.radius+J.radius;return J.center.distanceToSquared(this.center)<=Q*Q}intersectsBox(J){return J.intersectsSphere(this)}intersectsPlane(J){return Math.abs(J.distanceToPoint(this.center))<=this.radius}clampPoint(J,Q){let $=this.center.distanceToSquared(J);if(Q.copy(J),$>this.radius*this.radius)Q.sub(this.center).normalize(),Q.multiplyScalar(this.radius).add(this.center);return Q}getBoundingBox(J){if(this.isEmpty())return J.makeEmpty(),J;return J.set(this.center,this.center),J.expandByScalar(this.radius),J}applyMatrix4(J){return this.center.applyMatrix4(J),this.radius=this.radius*J.getMaxScaleOnAxis(),this}translate(J){return this.center.add(J),this}expandByPoint(J){if(this.isEmpty())return this.center.copy(J),this.radius=0,this;r9.subVectors(J,this.center);let Q=r9.lengthSq();if(Q>this.radius*this.radius){let $=Math.sqrt(Q),Z=($-this.radius)*0.5;this.center.addScaledVector(r9,Z/$),this.radius+=Z}return this}union(J){if(J.isEmpty())return this;if(this.isEmpty())return this.copy(J),this;if(this.center.equals(J.center)===!0)this.radius=Math.max(this.radius,J.radius);else QQ.subVectors(J.center,this.center).setLength(J.radius),this.expandByPoint(r9.copy(J.center).add(QQ)),this.expandByPoint(r9.copy(J.center).sub(QQ));return this}equals(J){return J.center.equals(this.center)&&J.radius===this.radius}clone(){return new this.constructor().copy(this)}toJSON(){return{radius:this.radius,center:this.center.toArray()}}fromJSON(J){return this.radius=J.radius,this.center.fromArray(J.center),this}}var O8=new A,$Q=new A,j6=new A,j8=new A,ZQ=new A,y6=new A,WQ=new A;class m8{constructor(J=new A,Q=new A(0,0,-1)){this.origin=J,this.direction=Q}set(J,Q){return this.origin.copy(J),this.direction.copy(Q),this}copy(J){return this.origin.copy(J.origin),this.direction.copy(J.direction),this}at(J,Q){return Q.copy(this.origin).addScaledVector(this.direction,J)}lookAt(J){return this.direction.copy(J).sub(this.origin).normalize(),this}recast(J){return this.origin.copy(this.at(J,O8)),this}closestPointToPoint(J,Q){Q.subVectors(J,this.origin);let $=Q.dot(this.direction);if($<0)return Q.copy(this.origin);return Q.copy(this.origin).addScaledVector(this.direction,$)}distanceToPoint(J){return Math.sqrt(this.distanceSqToPoint(J))}distanceSqToPoint(J){let Q=O8.subVectors(J,this.origin).dot(this.direction);if(Q<0)return this.origin.distanceToSquared(J);return O8.copy(this.origin).addScaledVector(this.direction,Q),O8.distanceToSquared(J)}distanceSqToSegment(J,Q,$,Z){$Q.copy(J).add(Q).multiplyScalar(0.5),j6.copy(Q).sub(J).normalize(),j8.copy(this.origin).sub($Q);let W=J.distanceTo(Q)*0.5,H=-this.direction.dot(j6),Y=j8.dot(this.direction),X=-j8.dot(j6),K=j8.lengthSq(),U=Math.abs(1-H*H),G,q,E,F;if(U>0)if(G=H*X-Y,q=H*Y-X,F=W*U,G>=0)if(q>=-F)if(q<=F){let k=1/U;G*=k,q*=k,E=G*(G+H*q+2*Y)+q*(H*G+q+2*X)+K}else q=W,G=Math.max(0,-(H*q+Y)),E=-G*G+q*(q+2*X)+K;else q=-W,G=Math.max(0,-(H*q+Y)),E=-G*G+q*(q+2*X)+K;else if(q<=-F)G=Math.max(0,-(-H*W+Y)),q=G>0?-W:Math.min(Math.max(-W,-X),W),E=-G*G+q*(q+2*X)+K;else if(q<=F)G=0,q=Math.min(Math.max(-W,-X),W),E=q*(q+2*X)+K;else G=Math.max(0,-(H*W+Y)),q=G>0?W:Math.min(Math.max(-W,-X),W),E=-G*G+q*(q+2*X)+K;else q=H>0?-W:W,G=Math.max(0,-(H*q+Y)),E=-G*G+q*(q+2*X)+K;if($)$.copy(this.origin).addScaledVector(this.direction,G);if(Z)Z.copy($Q).addScaledVector(j6,q);return E}intersectSphere(J,Q){O8.subVectors(J.center,this.origin);let $=O8.dot(this.direction),Z=O8.dot(O8)-$*$,W=J.radius*J.radius;if(Z>W)return null;let H=Math.sqrt(W-Z),Y=$-H,X=$+H;if(X<0)return null;if(Y<0)return this.at(X,Q);return this.at(Y,Q)}intersectsSphere(J){if(J.radius<0)return!1;return this.distanceSqToPoint(J.center)<=J.radius*J.radius}distanceToPlane(J){let Q=J.normal.dot(this.direction);if(Q===0){if(J.distanceToPoint(this.origin)===0)return 0;return null}let $=-(this.origin.dot(J.normal)+J.constant)/Q;return $>=0?$:null}intersectPlane(J,Q){let $=this.distanceToPlane(J);if($===null)return null;return this.at($,Q)}intersectsPlane(J){let Q=J.distanceToPoint(this.origin);if(Q===0)return!0;if(J.normal.dot(this.direction)*Q<0)return!0;return!1}intersectBox(J,Q){let $,Z,W,H,Y,X,K=1/this.direction.x,U=1/this.direction.y,G=1/this.direction.z,q=this.origin;if(K>=0)$=(J.min.x-q.x)*K,Z=(J.max.x-q.x)*K;else $=(J.max.x-q.x)*K,Z=(J.min.x-q.x)*K;if(U>=0)W=(J.min.y-q.y)*U,H=(J.max.y-q.y)*U;else W=(J.max.y-q.y)*U,H=(J.min.y-q.y)*U;if($>H||W>Z)return null;if(W>$||isNaN($))$=W;if(H<Z||isNaN(Z))Z=H;if(G>=0)Y=(J.min.z-q.z)*G,X=(J.max.z-q.z)*G;else Y=(J.max.z-q.z)*G,X=(J.min.z-q.z)*G;if($>X||Y>Z)return null;if(Y>$||$!==$)$=Y;if(X<Z||Z!==Z)Z=X;if(Z<0)return null;return this.at($>=0?$:Z,Q)}intersectsBox(J){return this.intersectBox(J,O8)!==null}intersectTriangle(J,Q,$,Z,W){ZQ.subVectors(Q,J),y6.subVectors($,J),WQ.crossVectors(ZQ,y6);let H=this.direction.dot(WQ),Y;if(H>0){if(Z)return null;Y=1}else if(H<0)Y=-1,H=-H;else return null;j8.subVectors(this.origin,J);let X=Y*this.direction.dot(y6.crossVectors(j8,y6));if(X<0)return null;let K=Y*this.direction.dot(ZQ.cross(j8));if(K<0)return null;if(X+K>H)return null;let U=-Y*j8.dot(WQ);if(U<0)return null;return this.at(U/H,W)}applyMatrix4(J){return this.origin.applyMatrix4(J),this.direction.transformDirection(J),this}equals(J){return J.origin.equals(this.origin)&&J.direction.equals(this.direction)}clone(){return new this.constructor().copy(this)}}class vJ{constructor(J,Q,$,Z,W,H,Y,X,K,U,G,q,E,F,k,M){if(vJ.prototype.isMatrix4=!0,this.elements=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1],J!==void 0)this.set(J,Q,$,Z,W,H,Y,X,K,U,G,q,E,F,k,M)}set(J,Q,$,Z,W,H,Y,X,K,U,G,q,E,F,k,M){let N=this.elements;return N[0]=J,N[4]=Q,N[8]=$,N[12]=Z,N[1]=W,N[5]=H,N[9]=Y,N[13]=X,N[2]=K,N[6]=U,N[10]=G,N[14]=q,N[3]=E,N[7]=F,N[11]=k,N[15]=M,this}identity(){return this.set(1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1),this}clone(){return new vJ().fromArray(this.elements)}copy(J){let Q=this.elements,$=J.elements;return Q[0]=$[0],Q[1]=$[1],Q[2]=$[2],Q[3]=$[3],Q[4]=$[4],Q[5]=$[5],Q[6]=$[6],Q[7]=$[7],Q[8]=$[8],Q[9]=$[9],Q[10]=$[10],Q[11]=$[11],Q[12]=$[12],Q[13]=$[13],Q[14]=$[14],Q[15]=$[15],this}copyPosition(J){let Q=this.elements,$=J.elements;return Q[12]=$[12],Q[13]=$[13],Q[14]=$[14],this}setFromMatrix3(J){let Q=J.elements;return this.set(Q[0],Q[3],Q[6],0,Q[1],Q[4],Q[7],0,Q[2],Q[5],Q[8],0,0,0,0,1),this}extractBasis(J,Q,$){return J.setFromMatrixColumn(this,0),Q.setFromMatrixColumn(this,1),$.setFromMatrixColumn(this,2),this}makeBasis(J,Q,$){return this.set(J.x,Q.x,$.x,0,J.y,Q.y,$.y,0,J.z,Q.z,$.z,0,0,0,0,1),this}extractRotation(J){let Q=this.elements,$=J.elements,Z=1/D9.setFromMatrixColumn(J,0).length(),W=1/D9.setFromMatrixColumn(J,1).length(),H=1/D9.setFromMatrixColumn(J,2).length();return Q[0]=$[0]*Z,Q[1]=$[1]*Z,Q[2]=$[2]*Z,Q[3]=0,Q[4]=$[4]*W,Q[5]=$[5]*W,Q[6]=$[6]*W,Q[7]=0,Q[8]=$[8]*H,Q[9]=$[9]*H,Q[10]=$[10]*H,Q[11]=0,Q[12]=0,Q[13]=0,Q[14]=0,Q[15]=1,this}makeRotationFromEuler(J){let Q=this.elements,$=J.x,Z=J.y,W=J.z,H=Math.cos($),Y=Math.sin($),X=Math.cos(Z),K=Math.sin(Z),U=Math.cos(W),G=Math.sin(W);if(J.order==="XYZ"){let q=H*U,E=H*G,F=Y*U,k=Y*G;Q[0]=X*U,Q[4]=-X*G,Q[8]=K,Q[1]=E+F*K,Q[5]=q-k*K,Q[9]=-Y*X,Q[2]=k-q*K,Q[6]=F+E*K,Q[10]=H*X}else if(J.order==="YXZ"){let q=X*U,E=X*G,F=K*U,k=K*G;Q[0]=q+k*Y,Q[4]=F*Y-E,Q[8]=H*K,Q[1]=H*G,Q[5]=H*U,Q[9]=-Y,Q[2]=E*Y-F,Q[6]=k+q*Y,Q[10]=H*X}else if(J.order==="ZXY"){let q=X*U,E=X*G,F=K*U,k=K*G;Q[0]=q-k*Y,Q[4]=-H*G,Q[8]=F+E*Y,Q[1]=E+F*Y,Q[5]=H*U,Q[9]=k-q*Y,Q[2]=-H*K,Q[6]=Y,Q[10]=H*X}else if(J.order==="ZYX"){let q=H*U,E=H*G,F=Y*U,k=Y*G;Q[0]=X*U,Q[4]=F*K-E,Q[8]=q*K+k,Q[1]=X*G,Q[5]=k*K+q,Q[9]=E*K-F,Q[2]=-K,Q[6]=Y*X,Q[10]=H*X}else if(J.order==="YZX"){let q=H*X,E=H*K,F=Y*X,k=Y*K;Q[0]=X*U,Q[4]=k-q*G,Q[8]=F*G+E,Q[1]=G,Q[5]=H*U,Q[9]=-Y*U,Q[2]=-K*U,Q[6]=E*G+F,Q[10]=q-k*G}else if(J.order==="XZY"){let q=H*X,E=H*K,F=Y*X,k=Y*K;Q[0]=X*U,Q[4]=-G,Q[8]=K*U,Q[1]=q*G+k,Q[5]=H*U,Q[9]=E*G-F,Q[2]=F*G-E,Q[6]=Y*U,Q[10]=k*G+q}return Q[3]=0,Q[7]=0,Q[11]=0,Q[12]=0,Q[13]=0,Q[14]=0,Q[15]=1,this}makeRotationFromQuaternion(J){return this.compose(hY,J,bY)}lookAt(J,Q,$){let Z=this.elements;if(f0.subVectors(J,Q),f0.lengthSq()===0)f0.z=1;if(f0.normalize(),y8.crossVectors($,f0),y8.lengthSq()===0){if(Math.abs($.z)===1)f0.x+=0.0001;else f0.z+=0.0001;f0.normalize(),y8.crossVectors($,f0)}return y8.normalize(),v6.crossVectors(f0,y8),Z[0]=y8.x,Z[4]=v6.x,Z[8]=f0.x,Z[1]=y8.y,Z[5]=v6.y,Z[9]=f0.y,Z[2]=y8.z,Z[6]=v6.z,Z[10]=f0.z,this}multiply(J){return this.multiplyMatrices(this,J)}premultiply(J){return this.multiplyMatrices(J,this)}multiplyMatrices(J,Q){let $=J.elements,Z=Q.elements,W=this.elements,H=$[0],Y=$[4],X=$[8],K=$[12],U=$[1],G=$[5],q=$[9],E=$[13],F=$[2],k=$[6],M=$[10],N=$[14],O=$[3],C=$[7],L=$[11],w=$[15],v=Z[0],_=Z[4],T=Z[8],x=Z[12],z=Z[1],V=Z[5],j=Z[9],m=Z[13],l=Z[2],c=Z[6],i=Z[10],u=Z[14],r=Z[3],g=Z[7],ZJ=Z[11],UJ=Z[15];return W[0]=H*v+Y*z+X*l+K*r,W[4]=H*_+Y*V+X*c+K*g,W[8]=H*T+Y*j+X*i+K*ZJ,W[12]=H*x+Y*m+X*u+K*UJ,W[1]=U*v+G*z+q*l+E*r,W[5]=U*_+G*V+q*c+E*g,W[9]=U*T+G*j+q*i+E*ZJ,W[13]=U*x+G*m+q*u+E*UJ,W[2]=F*v+k*z+M*l+N*r,W[6]=F*_+k*V+M*c+N*g,W[10]=F*T+k*j+M*i+N*ZJ,W[14]=F*x+k*m+M*u+N*UJ,W[3]=O*v+C*z+L*l+w*r,W[7]=O*_+C*V+L*c+w*g,W[11]=O*T+C*j+L*i+w*ZJ,W[15]=O*x+C*m+L*u+w*UJ,this}multiplyScalar(J){let Q=this.elements;return Q[0]*=J,Q[4]*=J,Q[8]*=J,Q[12]*=J,Q[1]*=J,Q[5]*=J,Q[9]*=J,Q[13]*=J,Q[2]*=J,Q[6]*=J,Q[10]*=J,Q[14]*=J,Q[3]*=J,Q[7]*=J,Q[11]*=J,Q[15]*=J,this}determinant(){let J=this.elements,Q=J[0],$=J[4],Z=J[8],W=J[12],H=J[1],Y=J[5],X=J[9],K=J[13],U=J[2],G=J[6],q=J[10],E=J[14],F=J[3],k=J[7],M=J[11],N=J[15];return F*(+W*X*G-Z*K*G-W*Y*q+$*K*q+Z*Y*E-$*X*E)+k*(+Q*X*E-Q*K*q+W*H*q-Z*H*E+Z*K*U-W*X*U)+M*(+Q*K*G-Q*Y*E-W*H*G+$*H*E+W*Y*U-$*K*U)+N*(-Z*Y*U-Q*X*G+Q*Y*q+Z*H*G-$*H*q+$*X*U)}transpose(){let J=this.elements,Q;return Q=J[1],J[1]=J[4],J[4]=Q,Q=J[2],J[2]=J[8],J[8]=Q,Q=J[6],J[6]=J[9],J[9]=Q,Q=J[3],J[3]=J[12],J[12]=Q,Q=J[7],J[7]=J[13],J[13]=Q,Q=J[11],J[11]=J[14],J[14]=Q,this}setPosition(J,Q,$){let Z=this.elements;if(J.isVector3)Z[12]=J.x,Z[13]=J.y,Z[14]=J.z;else Z[12]=J,Z[13]=Q,Z[14]=$;return this}invert(){let J=this.elements,Q=J[0],$=J[1],Z=J[2],W=J[3],H=J[4],Y=J[5],X=J[6],K=J[7],U=J[8],G=J[9],q=J[10],E=J[11],F=J[12],k=J[13],M=J[14],N=J[15],O=G*M*K-k*q*K+k*X*E-Y*M*E-G*X*N+Y*q*N,C=F*q*K-U*M*K-F*X*E+H*M*E+U*X*N-H*q*N,L=U*k*K-F*G*K+F*Y*E-H*k*E-U*Y*N+H*G*N,w=F*G*X-U*k*X-F*Y*q+H*k*q+U*Y*M-H*G*M,v=Q*O+$*C+Z*L+W*w;if(v===0)return this.set(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0);let _=1/v;return J[0]=O*_,J[1]=(k*q*W-G*M*W-k*Z*E+$*M*E+G*Z*N-$*q*N)*_,J[2]=(Y*M*W-k*X*W+k*Z*K-$*M*K-Y*Z*N+$*X*N)*_,J[3]=(G*X*W-Y*q*W-G*Z*K+$*q*K+Y*Z*E-$*X*E)*_,J[4]=C*_,J[5]=(U*M*W-F*q*W+F*Z*E-Q*M*E-U*Z*N+Q*q*N)*_,J[6]=(F*X*W-H*M*W-F*Z*K+Q*M*K+H*Z*N-Q*X*N)*_,J[7]=(H*q*W-U*X*W+U*Z*K-Q*q*K-H*Z*E+Q*X*E)*_,J[8]=L*_,J[9]=(F*G*W-U*k*W-F*$*E+Q*k*E+U*$*N-Q*G*N)*_,J[10]=(H*k*W-F*Y*W+F*$*K-Q*k*K-H*$*N+Q*Y*N)*_,J[11]=(U*Y*W-H*G*W-U*$*K+Q*G*K+H*$*E-Q*Y*E)*_,J[12]=w*_,J[13]=(U*k*Z-F*G*Z+F*$*q-Q*k*q-U*$*M+Q*G*M)*_,J[14]=(F*Y*Z-H*k*Z-F*$*X+Q*k*X+H*$*M-Q*Y*M)*_,J[15]=(H*G*Z-U*Y*Z+U*$*X-Q*G*X-H*$*q+Q*Y*q)*_,this}scale(J){let Q=this.elements,$=J.x,Z=J.y,W=J.z;return Q[0]*=$,Q[4]*=Z,Q[8]*=W,Q[1]*=$,Q[5]*=Z,Q[9]*=W,Q[2]*=$,Q[6]*=Z,Q[10]*=W,Q[3]*=$,Q[7]*=Z,Q[11]*=W,this}getMaxScaleOnAxis(){let J=this.elements,Q=J[0]*J[0]+J[1]*J[1]+J[2]*J[2],$=J[4]*J[4]+J[5]*J[5]+J[6]*J[6],Z=J[8]*J[8]+J[9]*J[9]+J[10]*J[10];return Math.sqrt(Math.max(Q,$,Z))}makeTranslation(J,Q,$){if(J.isVector3)this.set(1,0,0,J.x,0,1,0,J.y,0,0,1,J.z,0,0,0,1);else this.set(1,0,0,J,0,1,0,Q,0,0,1,$,0,0,0,1);return this}makeRotationX(J){let Q=Math.cos(J),$=Math.sin(J);return this.set(1,0,0,0,0,Q,-$,0,0,$,Q,0,0,0,0,1),this}makeRotationY(J){let Q=Math.cos(J),$=Math.sin(J);return this.set(Q,0,$,0,0,1,0,0,-$,0,Q,0,0,0,0,1),this}makeRotationZ(J){let Q=Math.cos(J),$=Math.sin(J);return this.set(Q,-$,0,0,$,Q,0,0,0,0,1,0,0,0,0,1),this}makeRotationAxis(J,Q){let $=Math.cos(Q),Z=Math.sin(Q),W=1-$,H=J.x,Y=J.y,X=J.z,K=W*H,U=W*Y;return this.set(K*H+$,K*Y-Z*X,K*X+Z*Y,0,K*Y+Z*X,U*Y+$,U*X-Z*H,0,K*X-Z*Y,U*X+Z*H,W*X*X+$,0,0,0,0,1),this}makeScale(J,Q,$){return this.set(J,0,0,0,0,Q,0,0,0,0,$,0,0,0,0,1),this}makeShear(J,Q,$,Z,W,H){return this.set(1,$,W,0,J,1,H,0,Q,Z,1,0,0,0,0,1),this}compose(J,Q,$){let Z=this.elements,W=Q._x,H=Q._y,Y=Q._z,X=Q._w,K=W+W,U=H+H,G=Y+Y,q=W*K,E=W*U,F=W*G,k=H*U,M=H*G,N=Y*G,O=X*K,C=X*U,L=X*G,w=$.x,v=$.y,_=$.z;return Z[0]=(1-(k+N))*w,Z[1]=(E+L)*w,Z[2]=(F-C)*w,Z[3]=0,Z[4]=(E-L)*v,Z[5]=(1-(q+N))*v,Z[6]=(M+O)*v,Z[7]=0,Z[8]=(F+C)*_,Z[9]=(M-O)*_,Z[10]=(1-(q+k))*_,Z[11]=0,Z[12]=J.x,Z[13]=J.y,Z[14]=J.z,Z[15]=1,this}decompose(J,Q,$){let Z=this.elements,W=D9.set(Z[0],Z[1],Z[2]).length(),H=D9.set(Z[4],Z[5],Z[6]).length(),Y=D9.set(Z[8],Z[9],Z[10]).length();if(this.determinant()<0)W=-W;J.x=Z[12],J.y=Z[13],J.z=Z[14],r0.copy(this);let K=1/W,U=1/H,G=1/Y;return r0.elements[0]*=K,r0.elements[1]*=K,r0.elements[2]*=K,r0.elements[4]*=U,r0.elements[5]*=U,r0.elements[6]*=U,r0.elements[8]*=G,r0.elements[9]*=G,r0.elements[10]*=G,Q.setFromRotationMatrix(r0),$.x=W,$.y=H,$.z=Y,this}makePerspective(J,Q,$,Z,W,H,Y=2000,X=!1){let K=this.elements,U=2*W/(Q-J),G=2*W/($-Z),q=(Q+J)/(Q-J),E=($+Z)/($-Z),F,k;if(X)F=W/(H-W),k=H*W/(H-W);else if(Y===2000)F=-(H+W)/(H-W),k=-2*H*W/(H-W);else if(Y===2001)F=-H/(H-W),k=-H*W/(H-W);else throw new Error("THREE.Matrix4.makePerspective(): Invalid coordinate system: "+Y);return K[0]=U,K[4]=0,K[8]=q,K[12]=0,K[1]=0,K[5]=G,K[9]=E,K[13]=0,K[2]=0,K[6]=0,K[10]=F,K[14]=k,K[3]=0,K[7]=0,K[11]=-1,K[15]=0,this}makeOrthographic(J,Q,$,Z,W,H,Y=2000,X=!1){let K=this.elements,U=2/(Q-J),G=2/($-Z),q=-(Q+J)/(Q-J),E=-($+Z)/($-Z),F,k;if(X)F=1/(H-W),k=H/(H-W);else if(Y===2000)F=-2/(H-W),k=-(H+W)/(H-W);else if(Y===2001)F=-1/(H-W),k=-W/(H-W);else throw new Error("THREE.Matrix4.makeOrthographic(): Invalid coordinate system: "+Y);return K[0]=U,K[4]=0,K[8]=0,K[12]=q,K[1]=0,K[5]=G,K[9]=0,K[13]=E,K[2]=0,K[6]=0,K[10]=F,K[14]=k,K[3]=0,K[7]=0,K[11]=0,K[15]=1,this}equals(J){let Q=this.elements,$=J.elements;for(let Z=0;Z<16;Z++)if(Q[Z]!==$[Z])return!1;return!0}fromArray(J,Q=0){for(let $=0;$<16;$++)this.elements[$]=J[$+Q];return this}toArray(J=[],Q=0){let $=this.elements;return J[Q]=$[0],J[Q+1]=$[1],J[Q+2]=$[2],J[Q+3]=$[3],J[Q+4]=$[4],J[Q+5]=$[5],J[Q+6]=$[6],J[Q+7]=$[7],J[Q+8]=$[8],J[Q+9]=$[9],J[Q+10]=$[10],J[Q+11]=$[11],J[Q+12]=$[12],J[Q+13]=$[13],J[Q+14]=$[14],J[Q+15]=$[15],J}}var D9=new A,r0=new vJ,hY=new A(0,0,0),bY=new A(1,1,1),y8=new A,v6=new A,f0=new A,qZ=new vJ,EZ=new A0;class $8{constructor(J=0,Q=0,$=0,Z=$8.DEFAULT_ORDER){this.isEuler=!0,this._x=J,this._y=Q,this._z=$,this._order=Z}get x(){return this._x}set x(J){this._x=J,this._onChangeCallback()}get y(){return this._y}set y(J){this._y=J,this._onChangeCallback()}get z(){return this._z}set z(J){this._z=J,this._onChangeCallback()}get order(){return this._order}set order(J){this._order=J,this._onChangeCallback()}set(J,Q,$,Z=this._order){return this._x=J,this._y=Q,this._z=$,this._order=Z,this._onChangeCallback(),this}clone(){return new this.constructor(this._x,this._y,this._z,this._order)}copy(J){return this._x=J._x,this._y=J._y,this._z=J._z,this._order=J._order,this._onChangeCallback(),this}setFromRotationMatrix(J,Q=this._order,$=!0){let Z=J.elements,W=Z[0],H=Z[4],Y=Z[8],X=Z[1],K=Z[5],U=Z[9],G=Z[2],q=Z[6],E=Z[10];switch(Q){case"XYZ":if(this._y=Math.asin(xJ(Y,-1,1)),Math.abs(Y)<0.9999999)this._x=Math.atan2(-U,E),this._z=Math.atan2(-H,W);else this._x=Math.atan2(q,K),this._z=0;break;case"YXZ":if(this._x=Math.asin(-xJ(U,-1,1)),Math.abs(U)<0.9999999)this._y=Math.atan2(Y,E),this._z=Math.atan2(X,K);else this._y=Math.atan2(-G,W),this._z=0;break;case"ZXY":if(this._x=Math.asin(xJ(q,-1,1)),Math.abs(q)<0.9999999)this._y=Math.atan2(-G,E),this._z=Math.atan2(-H,K);else this._y=0,this._z=Math.atan2(X,W);break;case"ZYX":if(this._y=Math.asin(-xJ(G,-1,1)),Math.abs(G)<0.9999999)this._x=Math.atan2(q,E),this._z=Math.atan2(X,W);else this._x=0,this._z=Math.atan2(-H,K);break;case"YZX":if(this._z=Math.asin(xJ(X,-1,1)),Math.abs(X)<0.9999999)this._x=Math.atan2(-U,K),this._y=Math.atan2(-G,W);else this._x=0,this._y=Math.atan2(Y,E);break;case"XZY":if(this._z=Math.asin(-xJ(H,-1,1)),Math.abs(H)<0.9999999)this._x=Math.atan2(q,K),this._y=Math.atan2(Y,W);else this._x=Math.atan2(-U,E),this._y=0;break;default:console.warn("THREE.Euler: .setFromRotationMatrix() encountered an unknown order: "+Q)}if(this._order=Q,$===!0)this._onChangeCallback();return this}setFromQuaternion(J,Q,$){return qZ.makeRotationFromQuaternion(J),this.setFromRotationMatrix(qZ,Q,$)}setFromVector3(J,Q=this._order){return this.set(J.x,J.y,J.z,Q)}reorder(J){return EZ.setFromEuler(this),this.setFromQuaternion(EZ,J)}equals(J){return J._x===this._x&&J._y===this._y&&J._z===this._z&&J._order===this._order}fromArray(J){if(this._x=J[0],this._y=J[1],this._z=J[2],J[3]!==void 0)this._order=J[3];return this._onChangeCallback(),this}toArray(J=[],Q=0){return J[Q]=this._x,J[Q+1]=this._y,J[Q+2]=this._z,J[Q+3]=this._order,J}_onChange(J){return this._onChangeCallback=J,this}_onChangeCallback(){}*[Symbol.iterator](){yield this._x,yield this._y,yield this._z,yield this._order}}$8.DEFAULT_ORDER="XYZ";class V7{constructor(){this.mask=1}set(J){this.mask=(1<<J|0)>>>0}enable(J){this.mask|=1<<J|0}enableAll(){this.mask=-1}toggle(J){this.mask^=1<<J|0}disable(J){this.mask&=~(1<<J|0)}disableAll(){this.mask=0}test(J){return(this.mask&J.mask)!==0}isEnabled(J){return(this.mask&(1<<J|0))!==0}}var xY=0,NZ=new A,L9=new A0,F8=new vJ,f6=new A,t9=new A,gY=new A,pY=new A0,OZ=new A(1,0,0),FZ=new A(0,1,0),RZ=new A(0,0,1),kZ={type:"added"},lY={type:"removed"},V9={type:"childadded",child:null},HQ={type:"childremoved",child:null};class Z0 extends w8{constructor(){super();this.isObject3D=!0,Object.defineProperty(this,"id",{value:xY++}),this.uuid=Q8(),this.name="",this.type="Object3D",this.parent=null,this.children=[],this.up=Z0.DEFAULT_UP.clone();let J=new A,Q=new $8,$=new A0,Z=new A(1,1,1);function W(){$.setFromEuler(Q,!1)}function H(){Q.setFromQuaternion($,void 0,!1)}Q._onChange(W),$._onChange(H),Object.defineProperties(this,{position:{configurable:!0,enumerable:!0,value:J},rotation:{configurable:!0,enumerable:!0,value:Q},quaternion:{configurable:!0,enumerable:!0,value:$},scale:{configurable:!0,enumerable:!0,value:Z},modelViewMatrix:{value:new vJ},normalMatrix:{value:new fJ}}),this.matrix=new vJ,this.matrixWorld=new vJ,this.matrixAutoUpdate=Z0.DEFAULT_MATRIX_AUTO_UPDATE,this.matrixWorldAutoUpdate=Z0.DEFAULT_MATRIX_WORLD_AUTO_UPDATE,this.matrixWorldNeedsUpdate=!1,this.layers=new V7,this.visible=!0,this.castShadow=!1,this.receiveShadow=!1,this.frustumCulled=!0,this.renderOrder=0,this.animations=[],this.customDepthMaterial=void 0,this.customDistanceMaterial=void 0,this.userData={}}onBeforeShadow(){}onAfterShadow(){}onBeforeRender(){}onAfterRender(){}applyMatrix4(J){if(this.matrixAutoUpdate)this.updateMatrix();this.matrix.premultiply(J),this.matrix.decompose(this.position,this.quaternion,this.scale)}applyQuaternion(J){return this.quaternion.premultiply(J),this}setRotationFromAxisAngle(J,Q){this.quaternion.setFromAxisAngle(J,Q)}setRotationFromEuler(J){this.quaternion.setFromEuler(J,!0)}setRotationFromMatrix(J){this.quaternion.setFromRotationMatrix(J)}setRotationFromQuaternion(J){this.quaternion.copy(J)}rotateOnAxis(J,Q){return L9.setFromAxisAngle(J,Q),this.quaternion.multiply(L9),this}rotateOnWorldAxis(J,Q){return L9.setFromAxisAngle(J,Q),this.quaternion.premultiply(L9),this}rotateX(J){return this.rotateOnAxis(OZ,J)}rotateY(J){return this.rotateOnAxis(FZ,J)}rotateZ(J){return this.rotateOnAxis(RZ,J)}translateOnAxis(J,Q){return NZ.copy(J).applyQuaternion(this.quaternion),this.position.add(NZ.multiplyScalar(Q)),this}translateX(J){return this.translateOnAxis(OZ,J)}translateY(J){return this.translateOnAxis(FZ,J)}translateZ(J){return this.translateOnAxis(RZ,J)}localToWorld(J){return this.updateWorldMatrix(!0,!1),J.applyMatrix4(this.matrixWorld)}worldToLocal(J){return this.updateWorldMatrix(!0,!1),J.applyMatrix4(F8.copy(this.matrixWorld).invert())}lookAt(J,Q,$){if(J.isVector3)f6.copy(J);else f6.set(J,Q,$);let Z=this.parent;if(this.updateWorldMatrix(!0,!1),t9.setFromMatrixPosition(this.matrixWorld),this.isCamera||this.isLight)F8.lookAt(t9,f6,this.up);else F8.lookAt(f6,t9,this.up);if(this.quaternion.setFromRotationMatrix(F8),Z)F8.extractRotation(Z.matrixWorld),L9.setFromRotationMatrix(F8),this.quaternion.premultiply(L9.invert())}add(J){if(arguments.length>1){for(let Q=0;Q<arguments.length;Q++)this.add(arguments[Q]);return this}if(J===this)return console.error("THREE.Object3D.add: object can't be added as a child of itself.",J),this;if(J&&J.isObject3D)J.removeFromParent(),J.parent=this,this.children.push(J),J.dispatchEvent(kZ),V9.child=J,this.dispatchEvent(V9),V9.child=null;else console.error("THREE.Object3D.add: object not an instance of THREE.Object3D.",J);return this}remove(J){if(arguments.length>1){for(let $=0;$<arguments.length;$++)this.remove(arguments[$]);return this}let Q=this.children.indexOf(J);if(Q!==-1)J.parent=null,this.children.splice(Q,1),J.dispatchEvent(lY),HQ.child=J,this.dispatchEvent(HQ),HQ.child=null;return this}removeFromParent(){let J=this.parent;if(J!==null)J.remove(this);return this}clear(){return this.remove(...this.children)}attach(J){if(this.updateWorldMatrix(!0,!1),F8.copy(this.matrixWorld).invert(),J.parent!==null)J.parent.updateWorldMatrix(!0,!1),F8.multiply(J.parent.matrixWorld);return J.applyMatrix4(F8),J.removeFromParent(),J.parent=this,this.children.push(J),J.updateWorldMatrix(!1,!0),J.dispatchEvent(kZ),V9.child=J,this.dispatchEvent(V9),V9.child=null,this}getObjectById(J){return this.getObjectByProperty("id",J)}getObjectByName(J){return this.getObjectByProperty("name",J)}getObjectByProperty(J,Q){if(this[J]===Q)return this;for(let $=0,Z=this.children.length;$<Z;$++){let H=this.children[$].getObjectByProperty(J,Q);if(H!==void 0)return H}return}getObjectsByProperty(J,Q,$=[]){if(this[J]===Q)$.push(this);let Z=this.children;for(let W=0,H=Z.length;W<H;W++)Z[W].getObjectsByProperty(J,Q,$);return $}getWorldPosition(J){return this.updateWorldMatrix(!0,!1),J.setFromMatrixPosition(this.matrixWorld)}getWorldQuaternion(J){return this.updateWorldMatrix(!0,!1),this.matrixWorld.decompose(t9,J,gY),J}getWorldScale(J){return this.updateWorldMatrix(!0,!1),this.matrixWorld.decompose(t9,pY,J),J}getWorldDirection(J){this.updateWorldMatrix(!0,!1);let Q=this.matrixWorld.elements;return J.set(Q[8],Q[9],Q[10]).normalize()}raycast(){}traverse(J){J(this);let Q=this.children;for(let $=0,Z=Q.length;$<Z;$++)Q[$].traverse(J)}traverseVisible(J){if(this.visible===!1)return;J(this);let Q=this.children;for(let $=0,Z=Q.length;$<Z;$++)Q[$].traverseVisible(J)}traverseAncestors(J){let Q=this.parent;if(Q!==null)J(Q),Q.traverseAncestors(J)}updateMatrix(){this.matrix.compose(this.position,this.quaternion,this.scale),this.matrixWorldNeedsUpdate=!0}updateMatrixWorld(J){if(this.matrixAutoUpdate)this.updateMatrix();if(this.matrixWorldNeedsUpdate||J){if(this.matrixWorldAutoUpdate===!0)if(this.parent===null)this.matrixWorld.copy(this.matrix);else this.matrixWorld.multiplyMatrices(this.parent.matrixWorld,this.matrix);this.matrixWorldNeedsUpdate=!1,J=!0}let Q=this.children;for(let $=0,Z=Q.length;$<Z;$++)Q[$].updateMatrixWorld(J)}updateWorldMatrix(J,Q){let $=this.parent;if(J===!0&&$!==null)$.updateWorldMatrix(!0,!1);if(this.matrixAutoUpdate)this.updateMatrix();if(this.matrixWorldAutoUpdate===!0)if(this.parent===null)this.matrixWorld.copy(this.matrix);else this.matrixWorld.multiplyMatrices(this.parent.matrixWorld,this.matrix);if(Q===!0){let Z=this.children;for(let W=0,H=Z.length;W<H;W++)Z[W].updateWorldMatrix(!1,!0)}}toJSON(J){let Q=J===void 0||typeof J==="string",$={};if(Q)J={geometries:{},materials:{},textures:{},images:{},shapes:{},skeletons:{},animations:{},nodes:{}},$.metadata={version:4.7,type:"Object",generator:"Object3D.toJSON"};let Z={};if(Z.uuid=this.uuid,Z.type=this.type,this.name!=="")Z.name=this.name;if(this.castShadow===!0)Z.castShadow=!0;if(this.receiveShadow===!0)Z.receiveShadow=!0;if(this.visible===!1)Z.visible=!1;if(this.frustumCulled===!1)Z.frustumCulled=!1;if(this.renderOrder!==0)Z.renderOrder=this.renderOrder;if(Object.keys(this.userData).length>0)Z.userData=this.userData;if(Z.layers=this.layers.mask,Z.matrix=this.matrix.toArray(),Z.up=this.up.toArray(),this.matrixAutoUpdate===!1)Z.matrixAutoUpdate=!1;if(this.isInstancedMesh){if(Z.type="InstancedMesh",Z.count=this.count,Z.instanceMatrix=this.instanceMatrix.toJSON(),this.instanceColor!==null)Z.instanceColor=this.instanceColor.toJSON()}if(this.isBatchedMesh){if(Z.type="BatchedMesh",Z.perObjectFrustumCulled=this.perObjectFrustumCulled,Z.sortObjects=this.sortObjects,Z.drawRanges=this._drawRanges,Z.reservedRanges=this._reservedRanges,Z.geometryInfo=this._geometryInfo.map((Y)=>({...Y,boundingBox:Y.boundingBox?Y.boundingBox.toJSON():void 0,boundingSphere:Y.boundingSphere?Y.boundingSphere.toJSON():void 0})),Z.instanceInfo=this._instanceInfo.map((Y)=>({...Y})),Z.availableInstanceIds=this._availableInstanceIds.slice(),Z.availableGeometryIds=this._availableGeometryIds.slice(),Z.nextIndexStart=this._nextIndexStart,Z.nextVertexStart=this._nextVertexStart,Z.geometryCount=this._geometryCount,Z.maxInstanceCount=this._maxInstanceCount,Z.maxVertexCount=this._maxVertexCount,Z.maxIndexCount=this._maxIndexCount,Z.geometryInitialized=this._geometryInitialized,Z.matricesTexture=this._matricesTexture.toJSON(J),Z.indirectTexture=this._indirectTexture.toJSON(J),this._colorsTexture!==null)Z.colorsTexture=this._colorsTexture.toJSON(J);if(this.boundingSphere!==null)Z.boundingSphere=this.boundingSphere.toJSON();if(this.boundingBox!==null)Z.boundingBox=this.boundingBox.toJSON()}function W(Y,X){if(Y[X.uuid]===void 0)Y[X.uuid]=X.toJSON(J);return X.uuid}if(this.isScene){if(this.background){if(this.background.isColor)Z.background=this.background.toJSON();else if(this.background.isTexture)Z.background=this.background.toJSON(J).uuid}if(this.environment&&this.environment.isTexture&&this.environment.isRenderTargetTexture!==!0)Z.environment=this.environment.toJSON(J).uuid}else if(this.isMesh||this.isLine||this.isPoints){Z.geometry=W(J.geometries,this.geometry);let Y=this.geometry.parameters;if(Y!==void 0&&Y.shapes!==void 0){let X=Y.shapes;if(Array.isArray(X))for(let K=0,U=X.length;K<U;K++){let G=X[K];W(J.shapes,G)}else W(J.shapes,X)}}if(this.isSkinnedMesh){if(Z.bindMode=this.bindMode,Z.bindMatrix=this.bindMatrix.toArray(),this.skeleton!==void 0)W(J.skeletons,this.skeleton),Z.skeleton=this.skeleton.uuid}if(this.material!==void 0)if(Array.isArray(this.material)){let Y=[];for(let X=0,K=this.material.length;X<K;X++)Y.push(W(J.materials,this.material[X]));Z.material=Y}else Z.material=W(J.materials,this.material);if(this.children.length>0){Z.children=[];for(let Y=0;Y<this.children.length;Y++)Z.children.push(this.children[Y].toJSON(J).object)}if(this.animations.length>0){Z.animations=[];for(let Y=0;Y<this.animations.length;Y++){let X=this.animations[Y];Z.animations.push(W(J.animations,X))}}if(Q){let Y=H(J.geometries),X=H(J.materials),K=H(J.textures),U=H(J.images),G=H(J.shapes),q=H(J.skeletons),E=H(J.animations),F=H(J.nodes);if(Y.length>0)$.geometries=Y;if(X.length>0)$.materials=X;if(K.length>0)$.textures=K;if(U.length>0)$.images=U;if(G.length>0)$.shapes=G;if(q.length>0)$.skeletons=q;if(E.length>0)$.animations=E;if(F.length>0)$.nodes=F}return $.object=Z,$;function H(Y){let X=[];for(let K in Y){let U=Y[K];delete U.metadata,X.push(U)}return X}}clone(J){return new this.constructor().copy(this,J)}copy(J,Q=!0){if(this.name=J.name,this.up.copy(J.up),this.position.copy(J.position),this.rotation.order=J.rotation.order,this.quaternion.copy(J.quaternion),this.scale.copy(J.scale),this.matrix.copy(J.matrix),this.matrixWorld.copy(J.matrixWorld),this.matrixAutoUpdate=J.matrixAutoUpdate,this.matrixWorldAutoUpdate=J.matrixWorldAutoUpdate,this.matrixWorldNeedsUpdate=J.matrixWorldNeedsUpdate,this.layers.mask=J.layers.mask,this.visible=J.visible,this.castShadow=J.castShadow,this.receiveShadow=J.receiveShadow,this.frustumCulled=J.frustumCulled,this.renderOrder=J.renderOrder,this.animations=J.animations.slice(),this.userData=JSON.parse(JSON.stringify(J.userData)),Q===!0)for(let $=0;$<J.children.length;$++){let Z=J.children[$];this.add(Z.clone())}return this}}Z0.DEFAULT_UP=new A(0,1,0);Z0.DEFAULT_MATRIX_AUTO_UPDATE=!0;Z0.DEFAULT_MATRIX_WORLD_AUTO_UPDATE=!0;var t0=new A,R8=new A,YQ=new A,k8=new A,z9=new A,B9=new A,MZ=new A,XQ=new A,KQ=new A,UQ=new A,GQ=new sJ,qQ=new sJ,EQ=new sJ;class n0{constructor(J=new A,Q=new A,$=new A){this.a=J,this.b=Q,this.c=$}static getNormal(J,Q,$,Z){Z.subVectors($,Q),t0.subVectors(J,Q),Z.cross(t0);let W=Z.lengthSq();if(W>0)return Z.multiplyScalar(1/Math.sqrt(W));return Z.set(0,0,0)}static getBarycoord(J,Q,$,Z,W){t0.subVectors(Z,Q),R8.subVectors($,Q),YQ.subVectors(J,Q);let H=t0.dot(t0),Y=t0.dot(R8),X=t0.dot(YQ),K=R8.dot(R8),U=R8.dot(YQ),G=H*K-Y*Y;if(G===0)return W.set(0,0,0),null;let q=1/G,E=(K*X-Y*U)*q,F=(H*U-Y*X)*q;return W.set(1-E-F,F,E)}static containsPoint(J,Q,$,Z){if(this.getBarycoord(J,Q,$,Z,k8)===null)return!1;return k8.x>=0&&k8.y>=0&&k8.x+k8.y<=1}static getInterpolation(J,Q,$,Z,W,H,Y,X){if(this.getBarycoord(J,Q,$,Z,k8)===null){if(X.x=0,X.y=0,"z"in X)X.z=0;if("w"in X)X.w=0;return null}return X.setScalar(0),X.addScaledVector(W,k8.x),X.addScaledVector(H,k8.y),X.addScaledVector(Y,k8.z),X}static getInterpolatedAttribute(J,Q,$,Z,W,H){return GQ.setScalar(0),qQ.setScalar(0),EQ.setScalar(0),GQ.fromBufferAttribute(J,Q),qQ.fromBufferAttribute(J,$),EQ.fromBufferAttribute(J,Z),H.setScalar(0),H.addScaledVector(GQ,W.x),H.addScaledVector(qQ,W.y),H.addScaledVector(EQ,W.z),H}static isFrontFacing(J,Q,$,Z){return t0.subVectors($,Q),R8.subVectors(J,Q),t0.cross(R8).dot(Z)<0?!0:!1}set(J,Q,$){return this.a.copy(J),this.b.copy(Q),this.c.copy($),this}setFromPointsAndIndices(J,Q,$,Z){return this.a.copy(J[Q]),this.b.copy(J[$]),this.c.copy(J[Z]),this}setFromAttributeAndIndices(J,Q,$,Z){return this.a.fromBufferAttribute(J,Q),this.b.fromBufferAttribute(J,$),this.c.fromBufferAttribute(J,Z),this}clone(){return new this.constructor().copy(this)}copy(J){return this.a.copy(J.a),this.b.copy(J.b),this.c.copy(J.c),this}getArea(){return t0.subVectors(this.c,this.b),R8.subVectors(this.a,this.b),t0.cross(R8).length()*0.5}getMidpoint(J){return J.addVectors(this.a,this.b).add(this.c).multiplyScalar(0.3333333333333333)}getNormal(J){return n0.getNormal(this.a,this.b,this.c,J)}getPlane(J){return J.setFromCoplanarPoints(this.a,this.b,this.c)}getBarycoord(J,Q){return n0.getBarycoord(J,this.a,this.b,this.c,Q)}getInterpolation(J,Q,$,Z,W){return n0.getInterpolation(J,this.a,this.b,this.c,Q,$,Z,W)}containsPoint(J){return n0.containsPoint(J,this.a,this.b,this.c)}isFrontFacing(J){return n0.isFrontFacing(this.a,this.b,this.c,J)}intersectsBox(J){return J.intersectsTriangle(this)}closestPointToPoint(J,Q){let $=this.a,Z=this.b,W=this.c,H,Y;z9.subVectors(Z,$),B9.subVectors(W,$),XQ.subVectors(J,$);let X=z9.dot(XQ),K=B9.dot(XQ);if(X<=0&&K<=0)return Q.copy($);KQ.subVectors(J,Z);let U=z9.dot(KQ),G=B9.dot(KQ);if(U>=0&&G<=U)return Q.copy(Z);let q=X*G-U*K;if(q<=0&&X>=0&&U<=0)return H=X/(X-U),Q.copy($).addScaledVector(z9,H);UQ.subVectors(J,W);let E=z9.dot(UQ),F=B9.dot(UQ);if(F>=0&&E<=F)return Q.copy(W);let k=E*K-X*F;if(k<=0&&K>=0&&F<=0)return Y=K/(K-F),Q.copy($).addScaledVector(B9,Y);let M=U*F-E*G;if(M<=0&&G-U>=0&&E-F>=0)return MZ.subVectors(W,Z),Y=(G-U)/(G-U+(E-F)),Q.copy(Z).addScaledVector(MZ,Y);let N=1/(M+k+q);return H=k*N,Y=q*N,Q.copy($).addScaledVector(z9,H).addScaledVector(B9,Y)}equals(J){return J.a.equals(this.a)&&J.b.equals(this.b)&&J.c.equals(this.c)}}var dW={aliceblue:15792383,antiquewhite:16444375,aqua:65535,aquamarine:8388564,azure:15794175,beige:16119260,bisque:16770244,black:0,blanchedalmond:16772045,blue:255,blueviolet:9055202,brown:10824234,burlywood:14596231,cadetblue:6266528,chartreuse:8388352,chocolate:13789470,coral:16744272,cornflowerblue:6591981,cornsilk:16775388,crimson:14423100,cyan:65535,darkblue:139,darkcyan:35723,darkgoldenrod:12092939,darkgray:11119017,darkgreen:25600,darkgrey:11119017,darkkhaki:12433259,darkmagenta:9109643,darkolivegreen:5597999,darkorange:16747520,darkorchid:10040012,darkred:9109504,darksalmon:15308410,darkseagreen:9419919,darkslateblue:4734347,darkslategray:3100495,darkslategrey:3100495,darkturquoise:52945,darkviolet:9699539,deeppink:16716947,deepskyblue:49151,dimgray:6908265,dimgrey:6908265,dodgerblue:2003199,firebrick:11674146,floralwhite:16775920,forestgreen:2263842,fuchsia:16711935,gainsboro:14474460,ghostwhite:16316671,gold:16766720,goldenrod:14329120,gray:8421504,green:32768,greenyellow:11403055,grey:8421504,honeydew:15794160,hotpink:16738740,indianred:13458524,indigo:4915330,ivory:16777200,khaki:15787660,lavender:15132410,lavenderblush:16773365,lawngreen:8190976,lemonchiffon:16775885,lightblue:11393254,lightcoral:15761536,lightcyan:14745599,lightgoldenrodyellow:16448210,lightgray:13882323,lightgreen:9498256,lightgrey:13882323,lightpink:16758465,lightsalmon:16752762,lightseagreen:2142890,lightskyblue:8900346,lightslategray:7833753,lightslategrey:7833753,lightsteelblue:11584734,lightyellow:16777184,lime:65280,limegreen:3329330,linen:16445670,magenta:16711935,maroon:8388608,mediumaquamarine:6737322,mediumblue:205,mediumorchid:12211667,mediumpurple:9662683,mediumseagreen:3978097,mediumslateblue:8087790,mediumspringgreen:64154,mediumturquoise:4772300,mediumvioletred:13047173,midnightblue:1644912,mintcream:16121850,mistyrose:16770273,moccasin:16770229,navajowhite:16768685,navy:128,oldlace:16643558,olive:8421376,olivedrab:7048739,orange:16753920,orangered:16729344,orchid:14315734,palegoldenrod:15657130,palegreen:10025880,paleturquoise:11529966,palevioletred:14381203,papayawhip:16773077,peachpuff:16767673,peru:13468991,pink:16761035,plum:14524637,powderblue:11591910,purple:8388736,rebeccapurple:6697881,red:16711680,rosybrown:12357519,royalblue:4286945,saddlebrown:9127187,salmon:16416882,sandybrown:16032864,seagreen:3050327,seashell:16774638,sienna:10506797,silver:12632256,skyblue:8900331,slateblue:6970061,slategray:7372944,slategrey:7372944,snow:16775930,springgreen:65407,steelblue:4620980,tan:13808780,teal:32896,thistle:14204888,tomato:16737095,turquoise:4251856,violet:15631086,wheat:16113331,white:16777215,whitesmoke:16119285,yellow:16776960,yellowgreen:10145074},v8={h:0,s:0,l:0},h6={h:0,s:0,l:0};function NQ(J,Q,$){if($<0)$+=1;if($>1)$-=1;if($<0.16666666666666666)return J+(Q-J)*6*$;if($<0.5)return Q;if($<0.6666666666666666)return J+(Q-J)*6*(0.6666666666666666-$);return J}class jJ{constructor(J,Q,$){return this.isColor=!0,this.r=1,this.g=1,this.b=1,this.set(J,Q,$)}set(J,Q,$){if(Q===void 0&&$===void 0){let Z=J;if(Z&&Z.isColor)this.copy(Z);else if(typeof Z==="number")this.setHex(Z);else if(typeof Z==="string")this.setStyle(Z)}else this.setRGB(J,Q,$);return this}setScalar(J){return this.r=J,this.g=J,this.b=J,this}setHex(J,Q="srgb"){return J=Math.floor(J),this.r=(J>>16&255)/255,this.g=(J>>8&255)/255,this.b=(J&255)/255,lJ.colorSpaceToWorking(this,Q),this}setRGB(J,Q,$,Z=lJ.workingColorSpace){return this.r=J,this.g=Q,this.b=$,lJ.colorSpaceToWorking(this,Z),this}setHSL(J,Q,$,Z=lJ.workingColorSpace){if(J=N$(J,1),Q=xJ(Q,0,1),$=xJ($,0,1),Q===0)this.r=this.g=this.b=$;else{let W=$<=0.5?$*(1+Q):$+Q-$*Q,H=2*$-W;this.r=NQ(H,W,J+0.3333333333333333),this.g=NQ(H,W,J),this.b=NQ(H,W,J-0.3333333333333333)}return lJ.colorSpaceToWorking(this,Z),this}setStyle(J,Q="srgb"){function $(W){if(W===void 0)return;if(parseFloat(W)<1)console.warn("THREE.Color: Alpha component of "+J+" will be ignored.")}let Z;if(Z=/^(\w+)\(([^\)]*)\)/.exec(J)){let W,H=Z[1],Y=Z[2];switch(H){case"rgb":case"rgba":if(W=/^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(Y))return $(W[4]),this.setRGB(Math.min(255,parseInt(W[1],10))/255,Math.min(255,parseInt(W[2],10))/255,Math.min(255,parseInt(W[3],10))/255,Q);if(W=/^\s*(\d+)\%\s*,\s*(\d+)\%\s*,\s*(\d+)\%\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(Y))return $(W[4]),this.setRGB(Math.min(100,parseInt(W[1],10))/100,Math.min(100,parseInt(W[2],10))/100,Math.min(100,parseInt(W[3],10))/100,Q);break;case"hsl":case"hsla":if(W=/^\s*(\d*\.?\d+)\s*,\s*(\d*\.?\d+)\%\s*,\s*(\d*\.?\d+)\%\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(Y))return $(W[4]),this.setHSL(parseFloat(W[1])/360,parseFloat(W[2])/100,parseFloat(W[3])/100,Q);break;default:console.warn("THREE.Color: Unknown color model "+J)}}else if(Z=/^\#([A-Fa-f\d]+)$/.exec(J)){let W=Z[1],H=W.length;if(H===3)return this.setRGB(parseInt(W.charAt(0),16)/15,parseInt(W.charAt(1),16)/15,parseInt(W.charAt(2),16)/15,Q);else if(H===6)return this.setHex(parseInt(W,16),Q);else console.warn("THREE.Color: Invalid hex color "+J)}else if(J&&J.length>0)return this.setColorName(J,Q);return this}setColorName(J,Q="srgb"){let $=dW[J.toLowerCase()];if($!==void 0)this.setHex($,Q);else console.warn("THREE.Color: Unknown color "+J);return this}clone(){return new this.constructor(this.r,this.g,this.b)}copy(J){return this.r=J.r,this.g=J.g,this.b=J.b,this}copySRGBToLinear(J){return this.r=D8(J.r),this.g=D8(J.g),this.b=D8(J.b),this}copyLinearToSRGB(J){return this.r=T9(J.r),this.g=T9(J.g),this.b=T9(J.b),this}convertSRGBToLinear(){return this.copySRGBToLinear(this),this}convertLinearToSRGB(){return this.copyLinearToSRGB(this),this}getHex(J="srgb"){return lJ.workingToColorSpace(B0.copy(this),J),Math.round(xJ(B0.r*255,0,255))*65536+Math.round(xJ(B0.g*255,0,255))*256+Math.round(xJ(B0.b*255,0,255))}getHexString(J="srgb"){return("000000"+this.getHex(J).toString(16)).slice(-6)}getHSL(J,Q=lJ.workingColorSpace){lJ.workingToColorSpace(B0.copy(this),Q);let{r:$,g:Z,b:W}=B0,H=Math.max($,Z,W),Y=Math.min($,Z,W),X,K,U=(Y+H)/2;if(Y===H)X=0,K=0;else{let G=H-Y;switch(K=U<=0.5?G/(H+Y):G/(2-H-Y),H){case $:X=(Z-W)/G+(Z<W?6:0);break;case Z:X=(W-$)/G+2;break;case W:X=($-Z)/G+4;break}X/=6}return J.h=X,J.s=K,J.l=U,J}getRGB(J,Q=lJ.workingColorSpace){return lJ.workingToColorSpace(B0.copy(this),Q),J.r=B0.r,J.g=B0.g,J.b=B0.b,J}getStyle(J="srgb"){lJ.workingToColorSpace(B0.copy(this),J);let{r:Q,g:$,b:Z}=B0;if(J!=="srgb")return`color(${J} ${Q.toFixed(3)} ${$.toFixed(3)} ${Z.toFixed(3)})`;return`rgb(${Math.round(Q*255)},${Math.round($*255)},${Math.round(Z*255)})`}offsetHSL(J,Q,$){return this.getHSL(v8),this.setHSL(v8.h+J,v8.s+Q,v8.l+$)}add(J){return this.r+=J.r,this.g+=J.g,this.b+=J.b,this}addColors(J,Q){return this.r=J.r+Q.r,this.g=J.g+Q.g,this.b=J.b+Q.b,this}addScalar(J){return this.r+=J,this.g+=J,this.b+=J,this}sub(J){return this.r=Math.max(0,this.r-J.r),this.g=Math.max(0,this.g-J.g),this.b=Math.max(0,this.b-J.b),this}multiply(J){return this.r*=J.r,this.g*=J.g,this.b*=J.b,this}multiplyScalar(J){return this.r*=J,this.g*=J,this.b*=J,this}lerp(J,Q){return this.r+=(J.r-this.r)*Q,this.g+=(J.g-this.g)*Q,this.b+=(J.b-this.b)*Q,this}lerpColors(J,Q,$){return this.r=J.r+(Q.r-J.r)*$,this.g=J.g+(Q.g-J.g)*$,this.b=J.b+(Q.b-J.b)*$,this}lerpHSL(J,Q){this.getHSL(v8),J.getHSL(h6);let $=H6(v8.h,h6.h,Q),Z=H6(v8.s,h6.s,Q),W=H6(v8.l,h6.l,Q);return this.setHSL($,Z,W),this}setFromVector3(J){return this.r=J.x,this.g=J.y,this.b=J.z,this}applyMatrix3(J){let Q=this.r,$=this.g,Z=this.b,W=J.elements;return this.r=W[0]*Q+W[3]*$+W[6]*Z,this.g=W[1]*Q+W[4]*$+W[7]*Z,this.b=W[2]*Q+W[5]*$+W[8]*Z,this}equals(J){return J.r===this.r&&J.g===this.g&&J.b===this.b}fromArray(J,Q=0){return this.r=J[Q],this.g=J[Q+1],this.b=J[Q+2],this}toArray(J=[],Q=0){return J[Q]=this.r,J[Q+1]=this.g,J[Q+2]=this.b,J}fromBufferAttribute(J,Q){return this.r=J.getX(Q),this.g=J.getY(Q),this.b=J.getZ(Q),this}toJSON(){return this.getHex()}*[Symbol.iterator](){yield this.r,yield this.g,yield this.b}}var B0=new jJ;jJ.NAMES=dW;var dY=0;class g0 extends w8{constructor(){super();this.isMaterial=!0,Object.defineProperty(this,"id",{value:dY++}),this.uuid=Q8(),this.name="",this.type="Material",this.blending=1,this.side=0,this.vertexColors=!1,this.opacity=1,this.transparent=!1,this.alphaHash=!1,this.blendSrc=204,this.blendDst=205,this.blendEquation=100,this.blendSrcAlpha=null,this.blendDstAlpha=null,this.blendEquationAlpha=null,this.blendColor=new jJ(0,0,0),this.blendAlpha=0,this.depthFunc=3,this.depthTest=!0,this.depthWrite=!0,this.stencilWriteMask=255,this.stencilFunc=519,this.stencilRef=0,this.stencilFuncMask=255,this.stencilFail=7680,this.stencilZFail=7680,this.stencilZPass=7680,this.stencilWrite=!1,this.clippingPlanes=null,this.clipIntersection=!1,this.clipShadows=!1,this.shadowSide=null,this.colorWrite=!0,this.precision=null,this.polygonOffset=!1,this.polygonOffsetFactor=0,this.polygonOffsetUnits=0,this.dithering=!1,this.alphaToCoverage=!1,this.premultipliedAlpha=!1,this.forceSinglePass=!1,this.allowOverride=!0,this.visible=!0,this.toneMapped=!0,this.userData={},this.version=0,this._alphaTest=0}get alphaTest(){return this._alphaTest}set alphaTest(J){if(this._alphaTest>0!==J>0)this.version++;this._alphaTest=J}onBeforeRender(){}onBeforeCompile(){}customProgramCacheKey(){return this.onBeforeCompile.toString()}setValues(J){if(J===void 0)return;for(let Q in J){let $=J[Q];if($===void 0){console.warn(`THREE.Material: parameter '${Q}' has value of undefined.`);continue}let Z=this[Q];if(Z===void 0){console.warn(`THREE.Material: '${Q}' is not a property of THREE.${this.type}.`);continue}if(Z&&Z.isColor)Z.set($);else if(Z&&Z.isVector3&&($&&$.isVector3))Z.copy($);else this[Q]=$}}toJSON(J){let Q=J===void 0||typeof J==="string";if(Q)J={textures:{},images:{}};let $={metadata:{version:4.7,type:"Material",generator:"Material.toJSON"}};if($.uuid=this.uuid,$.type=this.type,this.name!=="")$.name=this.name;if(this.color&&this.color.isColor)$.color=this.color.getHex();if(this.roughness!==void 0)$.roughness=this.roughness;if(this.metalness!==void 0)$.metalness=this.metalness;if(this.sheen!==void 0)$.sheen=this.sheen;if(this.sheenColor&&this.sheenColor.isColor)$.sheenColor=this.sheenColor.getHex();if(this.sheenRoughness!==void 0)$.sheenRoughness=this.sheenRoughness;if(this.emissive&&this.emissive.isColor)$.emissive=this.emissive.getHex();if(this.emissiveIntensity!==void 0&&this.emissiveIntensity!==1)$.emissiveIntensity=this.emissiveIntensity;if(this.specular&&this.specular.isColor)$.specular=this.specular.getHex();if(this.specularIntensity!==void 0)$.specularIntensity=this.specularIntensity;if(this.specularColor&&this.specularColor.isColor)$.specularColor=this.specularColor.getHex();if(this.shininess!==void 0)$.shininess=this.shininess;if(this.clearcoat!==void 0)$.clearcoat=this.clearcoat;if(this.clearcoatRoughness!==void 0)$.clearcoatRoughness=this.clearcoatRoughness;if(this.clearcoatMap&&this.clearcoatMap.isTexture)$.clearcoatMap=this.clearcoatMap.toJSON(J).uuid;if(this.clearcoatRoughnessMap&&this.clearcoatRoughnessMap.isTexture)$.clearcoatRoughnessMap=this.clearcoatRoughnessMap.toJSON(J).uuid;if(this.clearcoatNormalMap&&this.clearcoatNormalMap.isTexture)$.clearcoatNormalMap=this.clearcoatNormalMap.toJSON(J).uuid,$.clearcoatNormalScale=this.clearcoatNormalScale.toArray();if(this.dispersion!==void 0)$.dispersion=this.dispersion;if(this.iridescence!==void 0)$.iridescence=this.iridescence;if(this.iridescenceIOR!==void 0)$.iridescenceIOR=this.iridescenceIOR;if(this.iridescenceThicknessRange!==void 0)$.iridescenceThicknessRange=this.iridescenceThicknessRange;if(this.iridescenceMap&&this.iridescenceMap.isTexture)$.iridescenceMap=this.iridescenceMap.toJSON(J).uuid;if(this.iridescenceThicknessMap&&this.iridescenceThicknessMap.isTexture)$.iridescenceThicknessMap=this.iridescenceThicknessMap.toJSON(J).uuid;if(this.anisotropy!==void 0)$.anisotropy=this.anisotropy;if(this.anisotropyRotation!==void 0)$.anisotropyRotation=this.anisotropyRotation;if(this.anisotropyMap&&this.anisotropyMap.isTexture)$.anisotropyMap=this.anisotropyMap.toJSON(J).uuid;if(this.map&&this.map.isTexture)$.map=this.map.toJSON(J).uuid;if(this.matcap&&this.matcap.isTexture)$.matcap=this.matcap.toJSON(J).uuid;if(this.alphaMap&&this.alphaMap.isTexture)$.alphaMap=this.alphaMap.toJSON(J).uuid;if(this.lightMap&&this.lightMap.isTexture)$.lightMap=this.lightMap.toJSON(J).uuid,$.lightMapIntensity=this.lightMapIntensity;if(this.aoMap&&this.aoMap.isTexture)$.aoMap=this.aoMap.toJSON(J).uuid,$.aoMapIntensity=this.aoMapIntensity;if(this.bumpMap&&this.bumpMap.isTexture)$.bumpMap=this.bumpMap.toJSON(J).uuid,$.bumpScale=this.bumpScale;if(this.normalMap&&this.normalMap.isTexture)$.normalMap=this.normalMap.toJSON(J).uuid,$.normalMapType=this.normalMapType,$.normalScale=this.normalScale.toArray();if(this.displacementMap&&this.displacementMap.isTexture)$.displacementMap=this.displacementMap.toJSON(J).uuid,$.displacementScale=this.displacementScale,$.displacementBias=this.displacementBias;if(this.roughnessMap&&this.roughnessMap.isTexture)$.roughnessMap=this.roughnessMap.toJSON(J).uuid;if(this.metalnessMap&&this.metalnessMap.isTexture)$.metalnessMap=this.metalnessMap.toJSON(J).uuid;if(this.emissiveMap&&this.emissiveMap.isTexture)$.emissiveMap=this.emissiveMap.toJSON(J).uuid;if(this.specularMap&&this.specularMap.isTexture)$.specularMap=this.specularMap.toJSON(J).uuid;if(this.specularIntensityMap&&this.specularIntensityMap.isTexture)$.specularIntensityMap=this.specularIntensityMap.toJSON(J).uuid;if(this.specularColorMap&&this.specularColorMap.isTexture)$.specularColorMap=this.specularColorMap.toJSON(J).uuid;if(this.envMap&&this.envMap.isTexture){if($.envMap=this.envMap.toJSON(J).uuid,this.combine!==void 0)$.combine=this.combine}if(this.envMapRotation!==void 0)$.envMapRotation=this.envMapRotation.toArray();if(this.envMapIntensity!==void 0)$.envMapIntensity=this.envMapIntensity;if(this.reflectivity!==void 0)$.reflectivity=this.reflectivity;if(this.refractionRatio!==void 0)$.refractionRatio=this.refractionRatio;if(this.gradientMap&&this.gradientMap.isTexture)$.gradientMap=this.gradientMap.toJSON(J).uuid;if(this.transmission!==void 0)$.transmission=this.transmission;if(this.transmissionMap&&this.transmissionMap.isTexture)$.transmissionMap=this.transmissionMap.toJSON(J).uuid;if(this.thickness!==void 0)$.thickness=this.thickness;if(this.thicknessMap&&this.thicknessMap.isTexture)$.thicknessMap=this.thicknessMap.toJSON(J).uuid;if(this.attenuationDistance!==void 0&&this.attenuationDistance!==1/0)$.attenuationDistance=this.attenuationDistance;if(this.attenuationColor!==void 0)$.attenuationColor=this.attenuationColor.getHex();if(this.size!==void 0)$.size=this.size;if(this.shadowSide!==null)$.shadowSide=this.shadowSide;if(this.sizeAttenuation!==void 0)$.sizeAttenuation=this.sizeAttenuation;if(this.blending!==1)$.blending=this.blending;if(this.side!==0)$.side=this.side;if(this.vertexColors===!0)$.vertexColors=!0;if(this.opacity<1)$.opacity=this.opacity;if(this.transparent===!0)$.transparent=!0;if(this.blendSrc!==204)$.blendSrc=this.blendSrc;if(this.blendDst!==205)$.blendDst=this.blendDst;if(this.blendEquation!==100)$.blendEquation=this.blendEquation;if(this.blendSrcAlpha!==null)$.blendSrcAlpha=this.blendSrcAlpha;if(this.blendDstAlpha!==null)$.blendDstAlpha=this.blendDstAlpha;if(this.blendEquationAlpha!==null)$.blendEquationAlpha=this.blendEquationAlpha;if(this.blendColor&&this.blendColor.isColor)$.blendColor=this.blendColor.getHex();if(this.blendAlpha!==0)$.blendAlpha=this.blendAlpha;if(this.depthFunc!==3)$.depthFunc=this.depthFunc;if(this.depthTest===!1)$.depthTest=this.depthTest;if(this.depthWrite===!1)$.depthWrite=this.depthWrite;if(this.colorWrite===!1)$.colorWrite=this.colorWrite;if(this.stencilWriteMask!==255)$.stencilWriteMask=this.stencilWriteMask;if(this.stencilFunc!==519)$.stencilFunc=this.stencilFunc;if(this.stencilRef!==0)$.stencilRef=this.stencilRef;if(this.stencilFuncMask!==255)$.stencilFuncMask=this.stencilFuncMask;if(this.stencilFail!==7680)$.stencilFail=this.stencilFail;if(this.stencilZFail!==7680)$.stencilZFail=this.stencilZFail;if(this.stencilZPass!==7680)$.stencilZPass=this.stencilZPass;if(this.stencilWrite===!0)$.stencilWrite=this.stencilWrite;if(this.rotation!==void 0&&this.rotation!==0)$.rotation=this.rotation;if(this.polygonOffset===!0)$.polygonOffset=!0;if(this.polygonOffsetFactor!==0)$.polygonOffsetFactor=this.polygonOffsetFactor;if(this.polygonOffsetUnits!==0)$.polygonOffsetUnits=this.polygonOffsetUnits;if(this.linewidth!==void 0&&this.linewidth!==1)$.linewidth=this.linewidth;if(this.dashSize!==void 0)$.dashSize=this.dashSize;if(this.gapSize!==void 0)$.gapSize=this.gapSize;if(this.scale!==void 0)$.scale=this.scale;if(this.dithering===!0)$.dithering=!0;if(this.alphaTest>0)$.alphaTest=this.alphaTest;if(this.alphaHash===!0)$.alphaHash=!0;if(this.alphaToCoverage===!0)$.alphaToCoverage=!0;if(this.premultipliedAlpha===!0)$.premultipliedAlpha=!0;if(this.forceSinglePass===!0)$.forceSinglePass=!0;if(this.wireframe===!0)$.wireframe=!0;if(this.wireframeLinewidth>1)$.wireframeLinewidth=this.wireframeLinewidth;if(this.wireframeLinecap!=="round")$.wireframeLinecap=this.wireframeLinecap;if(this.wireframeLinejoin!=="round")$.wireframeLinejoin=this.wireframeLinejoin;if(this.flatShading===!0)$.flatShading=!0;if(this.visible===!1)$.visible=!1;if(this.toneMapped===!1)$.toneMapped=!1;if(this.fog===!1)$.fog=!1;if(Object.keys(this.userData).length>0)$.userData=this.userData;function Z(W){let H=[];for(let Y in W){let X=W[Y];delete X.metadata,H.push(X)}return H}if(Q){let W=Z(J.textures),H=Z(J.images);if(W.length>0)$.textures=W;if(H.length>0)$.images=H}return $}clone(){return new this.constructor().copy(this)}copy(J){this.name=J.name,this.blending=J.blending,this.side=J.side,this.vertexColors=J.vertexColors,this.opacity=J.opacity,this.transparent=J.transparent,this.blendSrc=J.blendSrc,this.blendDst=J.blendDst,this.blendEquation=J.blendEquation,this.blendSrcAlpha=J.blendSrcAlpha,this.blendDstAlpha=J.blendDstAlpha,this.blendEquationAlpha=J.blendEquationAlpha,this.blendColor.copy(J.blendColor),this.blendAlpha=J.blendAlpha,this.depthFunc=J.depthFunc,this.depthTest=J.depthTest,this.depthWrite=J.depthWrite,this.stencilWriteMask=J.stencilWriteMask,this.stencilFunc=J.stencilFunc,this.stencilRef=J.stencilRef,this.stencilFuncMask=J.stencilFuncMask,this.stencilFail=J.stencilFail,this.stencilZFail=J.stencilZFail,this.stencilZPass=J.stencilZPass,this.stencilWrite=J.stencilWrite;let Q=J.clippingPlanes,$=null;if(Q!==null){let Z=Q.length;$=new Array(Z);for(let W=0;W!==Z;++W)$[W]=Q[W].clone()}return this.clippingPlanes=$,this.clipIntersection=J.clipIntersection,this.clipShadows=J.clipShadows,this.shadowSide=J.shadowSide,this.colorWrite=J.colorWrite,this.precision=J.precision,this.polygonOffset=J.polygonOffset,this.polygonOffsetFactor=J.polygonOffsetFactor,this.polygonOffsetUnits=J.polygonOffsetUnits,this.dithering=J.dithering,this.alphaTest=J.alphaTest,this.alphaHash=J.alphaHash,this.alphaToCoverage=J.alphaToCoverage,this.premultipliedAlpha=J.premultipliedAlpha,this.forceSinglePass=J.forceSinglePass,this.visible=J.visible,this.toneMapped=J.toneMapped,this.userData=JSON.parse(JSON.stringify(J.userData)),this}dispose(){this.dispatchEvent({type:"dispose"})}set needsUpdate(J){if(J===!0)this.version++}}class G8 extends g0{constructor(J){super();this.isMeshBasicMaterial=!0,this.type="MeshBasicMaterial",this.color=new jJ(16777215),this.map=null,this.lightMap=null,this.lightMapIntensity=1,this.aoMap=null,this.aoMapIntensity=1,this.specularMap=null,this.alphaMap=null,this.envMap=null,this.envMapRotation=new $8,this.combine=0,this.reflectivity=1,this.refractionRatio=0.98,this.wireframe=!1,this.wireframeLinewidth=1,this.wireframeLinecap="round",this.wireframeLinejoin="round",this.fog=!0,this.setValues(J)}copy(J){return super.copy(J),this.color.copy(J.color),this.map=J.map,this.lightMap=J.lightMap,this.lightMapIntensity=J.lightMapIntensity,this.aoMap=J.aoMap,this.aoMapIntensity=J.aoMapIntensity,this.specularMap=J.specularMap,this.alphaMap=J.alphaMap,this.envMap=J.envMap,this.envMapRotation.copy(J.envMapRotation),this.combine=J.combine,this.reflectivity=J.reflectivity,this.refractionRatio=J.refractionRatio,this.wireframe=J.wireframe,this.wireframeLinewidth=J.wireframeLinewidth,this.wireframeLinecap=J.wireframeLinecap,this.wireframeLinejoin=J.wireframeLinejoin,this.fog=J.fog,this}}var q0=new A,b6=new PJ,mY=0;class F0{constructor(J,Q,$=!1){if(Array.isArray(J))throw new TypeError("THREE.BufferAttribute: array should be a Typed Array.");this.isBufferAttribute=!0,Object.defineProperty(this,"id",{value:mY++}),this.name="",this.array=J,this.itemSize=Q,this.count=J!==void 0?J.length/Q:0,this.normalized=$,this.usage=35044,this.updateRanges=[],this.gpuType=1015,this.version=0}onUploadCallback(){}set needsUpdate(J){if(J===!0)this.version++}setUsage(J){return this.usage=J,this}addUpdateRange(J,Q){this.updateRanges.push({start:J,count:Q})}clearUpdateRanges(){this.updateRanges.length=0}copy(J){return this.name=J.name,this.array=new J.array.constructor(J.array),this.itemSize=J.itemSize,this.count=J.count,this.normalized=J.normalized,this.usage=J.usage,this.gpuType=J.gpuType,this}copyAt(J,Q,$){J*=this.itemSize,$*=Q.itemSize;for(let Z=0,W=this.itemSize;Z<W;Z++)this.array[J+Z]=Q.array[$+Z];return this}copyArray(J){return this.array.set(J),this}applyMatrix3(J){if(this.itemSize===2)for(let Q=0,$=this.count;Q<$;Q++)b6.fromBufferAttribute(this,Q),b6.applyMatrix3(J),this.setXY(Q,b6.x,b6.y);else if(this.itemSize===3)for(let Q=0,$=this.count;Q<$;Q++)q0.fromBufferAttribute(this,Q),q0.applyMatrix3(J),this.setXYZ(Q,q0.x,q0.y,q0.z);return this}applyMatrix4(J){for(let Q=0,$=this.count;Q<$;Q++)q0.fromBufferAttribute(this,Q),q0.applyMatrix4(J),this.setXYZ(Q,q0.x,q0.y,q0.z);return this}applyNormalMatrix(J){for(let Q=0,$=this.count;Q<$;Q++)q0.fromBufferAttribute(this,Q),q0.applyNormalMatrix(J),this.setXYZ(Q,q0.x,q0.y,q0.z);return this}transformDirection(J){for(let Q=0,$=this.count;Q<$;Q++)q0.fromBufferAttribute(this,Q),q0.transformDirection(J),this.setXYZ(Q,q0.x,q0.y,q0.z);return this}set(J,Q=0){return this.array.set(J,Q),this}getComponent(J,Q){let $=this.array[J*this.itemSize+Q];if(this.normalized)$=J8($,this.array);return $}setComponent(J,Q,$){if(this.normalized)$=aJ($,this.array);return this.array[J*this.itemSize+Q]=$,this}getX(J){let Q=this.array[J*this.itemSize];if(this.normalized)Q=J8(Q,this.array);return Q}setX(J,Q){if(this.normalized)Q=aJ(Q,this.array);return this.array[J*this.itemSize]=Q,this}getY(J){let Q=this.array[J*this.itemSize+1];if(this.normalized)Q=J8(Q,this.array);return Q}setY(J,Q){if(this.normalized)Q=aJ(Q,this.array);return this.array[J*this.itemSize+1]=Q,this}getZ(J){let Q=this.array[J*this.itemSize+2];if(this.normalized)Q=J8(Q,this.array);return Q}setZ(J,Q){if(this.normalized)Q=aJ(Q,this.array);return this.array[J*this.itemSize+2]=Q,this}getW(J){let Q=this.array[J*this.itemSize+3];if(this.normalized)Q=J8(Q,this.array);return Q}setW(J,Q){if(this.normalized)Q=aJ(Q,this.array);return this.array[J*this.itemSize+3]=Q,this}setXY(J,Q,$){if(J*=this.itemSize,this.normalized)Q=aJ(Q,this.array),$=aJ($,this.array);return this.array[J+0]=Q,this.array[J+1]=$,this}setXYZ(J,Q,$,Z){if(J*=this.itemSize,this.normalized)Q=aJ(Q,this.array),$=aJ($,this.array),Z=aJ(Z,this.array);return this.array[J+0]=Q,this.array[J+1]=$,this.array[J+2]=Z,this}setXYZW(J,Q,$,Z,W){if(J*=this.itemSize,this.normalized)Q=aJ(Q,this.array),$=aJ($,this.array),Z=aJ(Z,this.array),W=aJ(W,this.array);return this.array[J+0]=Q,this.array[J+1]=$,this.array[J+2]=Z,this.array[J+3]=W,this}onUpload(J){return this.onUploadCallback=J,this}clone(){return new this.constructor(this.array,this.itemSize).copy(this)}toJSON(){let J={itemSize:this.itemSize,type:this.array.constructor.name,array:Array.from(this.array),normalized:this.normalized};if(this.name!=="")J.name=this.name;if(this.usage!==35044)J.usage=this.usage;return J}}class z7 extends F0{constructor(J,Q,$){super(new Uint16Array(J),Q,$)}}class B7 extends F0{constructor(J,Q,$){super(new Uint32Array(J),Q,$)}}class s0 extends F0{constructor(J,Q,$){super(new Float32Array(J),Q,$)}}var uY=0,c0=new vJ,OQ=new Z0,C9=new A,h0=new S0,e9=new S0,L0=new A;class p0 extends w8{constructor(){super();this.isBufferGeometry=!0,Object.defineProperty(this,"id",{value:uY++}),this.uuid=Q8(),this.name="",this.type="BufferGeometry",this.index=null,this.indirect=null,this.attributes={},this.morphAttributes={},this.morphTargetsRelative=!1,this.groups=[],this.boundingBox=null,this.boundingSphere=null,this.drawRange={start:0,count:1/0},this.userData={}}getIndex(){return this.index}setIndex(J){if(Array.isArray(J))this.index=new((O$(J))?B7:z7)(J,1);else this.index=J;return this}setIndirect(J){return this.indirect=J,this}getIndirect(){return this.indirect}getAttribute(J){return this.attributes[J]}setAttribute(J,Q){return this.attributes[J]=Q,this}deleteAttribute(J){return delete this.attributes[J],this}hasAttribute(J){return this.attributes[J]!==void 0}addGroup(J,Q,$=0){this.groups.push({start:J,count:Q,materialIndex:$})}clearGroups(){this.groups=[]}setDrawRange(J,Q){this.drawRange.start=J,this.drawRange.count=Q}applyMatrix4(J){let Q=this.attributes.position;if(Q!==void 0)Q.applyMatrix4(J),Q.needsUpdate=!0;let $=this.attributes.normal;if($!==void 0){let W=new fJ().getNormalMatrix(J);$.applyNormalMatrix(W),$.needsUpdate=!0}let Z=this.attributes.tangent;if(Z!==void 0)Z.transformDirection(J),Z.needsUpdate=!0;if(this.boundingBox!==null)this.computeBoundingBox();if(this.boundingSphere!==null)this.computeBoundingSphere();return this}applyQuaternion(J){return c0.makeRotationFromQuaternion(J),this.applyMatrix4(c0),this}rotateX(J){return c0.makeRotationX(J),this.applyMatrix4(c0),this}rotateY(J){return c0.makeRotationY(J),this.applyMatrix4(c0),this}rotateZ(J){return c0.makeRotationZ(J),this.applyMatrix4(c0),this}translate(J,Q,$){return c0.makeTranslation(J,Q,$),this.applyMatrix4(c0),this}scale(J,Q,$){return c0.makeScale(J,Q,$),this.applyMatrix4(c0),this}lookAt(J){return OQ.lookAt(J),OQ.updateMatrix(),this.applyMatrix4(OQ.matrix),this}center(){return this.computeBoundingBox(),this.boundingBox.getCenter(C9).negate(),this.translate(C9.x,C9.y,C9.z),this}setFromPoints(J){let Q=this.getAttribute("position");if(Q===void 0){let $=[];for(let Z=0,W=J.length;Z<W;Z++){let H=J[Z];$.push(H.x,H.y,H.z||0)}this.setAttribute("position",new s0($,3))}else{let $=Math.min(J.length,Q.count);for(let Z=0;Z<$;Z++){let W=J[Z];Q.setXYZ(Z,W.x,W.y,W.z||0)}if(J.length>Q.count)console.warn("THREE.BufferGeometry: Buffer size too small for points data. Use .dispose() and create a new geometry.");Q.needsUpdate=!0}return this}computeBoundingBox(){if(this.boundingBox===null)this.boundingBox=new S0;let J=this.attributes.position,Q=this.morphAttributes.position;if(J&&J.isGLBufferAttribute){console.error("THREE.BufferGeometry.computeBoundingBox(): GLBufferAttribute requires a manual bounding box.",this),this.boundingBox.set(new A(-1/0,-1/0,-1/0),new A(1/0,1/0,1/0));return}if(J!==void 0){if(this.boundingBox.setFromBufferAttribute(J),Q)for(let $=0,Z=Q.length;$<Z;$++){let W=Q[$];if(h0.setFromBufferAttribute(W),this.morphTargetsRelative)L0.addVectors(this.boundingBox.min,h0.min),this.boundingBox.expandByPoint(L0),L0.addVectors(this.boundingBox.max,h0.max),this.boundingBox.expandByPoint(L0);else this.boundingBox.expandByPoint(h0.min),this.boundingBox.expandByPoint(h0.max)}}else this.boundingBox.makeEmpty();if(isNaN(this.boundingBox.min.x)||isNaN(this.boundingBox.min.y)||isNaN(this.boundingBox.min.z))console.error('THREE.BufferGeometry.computeBoundingBox(): Computed min/max have NaN values. The "position" attribute is likely to have NaN values.',this)}computeBoundingSphere(){if(this.boundingSphere===null)this.boundingSphere=new x0;let J=this.attributes.position,Q=this.morphAttributes.position;if(J&&J.isGLBufferAttribute){console.error("THREE.BufferGeometry.computeBoundingSphere(): GLBufferAttribute requires a manual bounding sphere.",this),this.boundingSphere.set(new A,1/0);return}if(J){let $=this.boundingSphere.center;if(h0.setFromBufferAttribute(J),Q)for(let W=0,H=Q.length;W<H;W++){let Y=Q[W];if(e9.setFromBufferAttribute(Y),this.morphTargetsRelative)L0.addVectors(h0.min,e9.min),h0.expandByPoint(L0),L0.addVectors(h0.max,e9.max),h0.expandByPoint(L0);else h0.expandByPoint(e9.min),h0.expandByPoint(e9.max)}h0.getCenter($);let Z=0;for(let W=0,H=J.count;W<H;W++)L0.fromBufferAttribute(J,W),Z=Math.max(Z,$.distanceToSquared(L0));if(Q)for(let W=0,H=Q.length;W<H;W++){let Y=Q[W],X=this.morphTargetsRelative;for(let K=0,U=Y.count;K<U;K++){if(L0.fromBufferAttribute(Y,K),X)C9.fromBufferAttribute(J,K),L0.add(C9);Z=Math.max(Z,$.distanceToSquared(L0))}}if(this.boundingSphere.radius=Math.sqrt(Z),isNaN(this.boundingSphere.radius))console.error('THREE.BufferGeometry.computeBoundingSphere(): Computed radius is NaN. The "position" attribute is likely to have NaN values.',this)}}computeTangents(){let J=this.index,Q=this.attributes;if(J===null||Q.position===void 0||Q.normal===void 0||Q.uv===void 0){console.error("THREE.BufferGeometry: .computeTangents() failed. Missing required attributes (index, position, normal or uv)");return}let{position:$,normal:Z,uv:W}=Q;if(this.hasAttribute("tangent")===!1)this.setAttribute("tangent",new F0(new Float32Array(4*$.count),4));let H=this.getAttribute("tangent"),Y=[],X=[];for(let T=0;T<$.count;T++)Y[T]=new A,X[T]=new A;let K=new A,U=new A,G=new A,q=new PJ,E=new PJ,F=new PJ,k=new A,M=new A;function N(T,x,z){K.fromBufferAttribute($,T),U.fromBufferAttribute($,x),G.fromBufferAttribute($,z),q.fromBufferAttribute(W,T),E.fromBufferAttribute(W,x),F.fromBufferAttribute(W,z),U.sub(K),G.sub(K),E.sub(q),F.sub(q);let V=1/(E.x*F.y-F.x*E.y);if(!isFinite(V))return;k.copy(U).multiplyScalar(F.y).addScaledVector(G,-E.y).multiplyScalar(V),M.copy(G).multiplyScalar(E.x).addScaledVector(U,-F.x).multiplyScalar(V),Y[T].add(k),Y[x].add(k),Y[z].add(k),X[T].add(M),X[x].add(M),X[z].add(M)}let O=this.groups;if(O.length===0)O=[{start:0,count:J.count}];for(let T=0,x=O.length;T<x;++T){let z=O[T],V=z.start,j=z.count;for(let m=V,l=V+j;m<l;m+=3)N(J.getX(m+0),J.getX(m+1),J.getX(m+2))}let C=new A,L=new A,w=new A,v=new A;function _(T){w.fromBufferAttribute(Z,T),v.copy(w);let x=Y[T];C.copy(x),C.sub(w.multiplyScalar(w.dot(x))).normalize(),L.crossVectors(v,x);let V=L.dot(X[T])<0?-1:1;H.setXYZW(T,C.x,C.y,C.z,V)}for(let T=0,x=O.length;T<x;++T){let z=O[T],V=z.start,j=z.count;for(let m=V,l=V+j;m<l;m+=3)_(J.getX(m+0)),_(J.getX(m+1)),_(J.getX(m+2))}}computeVertexNormals(){let J=this.index,Q=this.getAttribute("position");if(Q!==void 0){let $=this.getAttribute("normal");if($===void 0)$=new F0(new Float32Array(Q.count*3),3),this.setAttribute("normal",$);else for(let q=0,E=$.count;q<E;q++)$.setXYZ(q,0,0,0);let Z=new A,W=new A,H=new A,Y=new A,X=new A,K=new A,U=new A,G=new A;if(J)for(let q=0,E=J.count;q<E;q+=3){let F=J.getX(q+0),k=J.getX(q+1),M=J.getX(q+2);Z.fromBufferAttribute(Q,F),W.fromBufferAttribute(Q,k),H.fromBufferAttribute(Q,M),U.subVectors(H,W),G.subVectors(Z,W),U.cross(G),Y.fromBufferAttribute($,F),X.fromBufferAttribute($,k),K.fromBufferAttribute($,M),Y.add(U),X.add(U),K.add(U),$.setXYZ(F,Y.x,Y.y,Y.z),$.setXYZ(k,X.x,X.y,X.z),$.setXYZ(M,K.x,K.y,K.z)}else for(let q=0,E=Q.count;q<E;q+=3)Z.fromBufferAttribute(Q,q+0),W.fromBufferAttribute(Q,q+1),H.fromBufferAttribute(Q,q+2),U.subVectors(H,W),G.subVectors(Z,W),U.cross(G),$.setXYZ(q+0,U.x,U.y,U.z),$.setXYZ(q+1,U.x,U.y,U.z),$.setXYZ(q+2,U.x,U.y,U.z);this.normalizeNormals(),$.needsUpdate=!0}}normalizeNormals(){let J=this.attributes.normal;for(let Q=0,$=J.count;Q<$;Q++)L0.fromBufferAttribute(J,Q),L0.normalize(),J.setXYZ(Q,L0.x,L0.y,L0.z)}toNonIndexed(){function J(Y,X){let{array:K,itemSize:U,normalized:G}=Y,q=new K.constructor(X.length*U),E=0,F=0;for(let k=0,M=X.length;k<M;k++){if(Y.isInterleavedBufferAttribute)E=X[k]*Y.data.stride+Y.offset;else E=X[k]*U;for(let N=0;N<U;N++)q[F++]=K[E++]}return new F0(q,U,G)}if(this.index===null)return console.warn("THREE.BufferGeometry.toNonIndexed(): BufferGeometry is already non-indexed."),this;let Q=new p0,$=this.index.array,Z=this.attributes;for(let Y in Z){let X=Z[Y],K=J(X,$);Q.setAttribute(Y,K)}let W=this.morphAttributes;for(let Y in W){let X=[],K=W[Y];for(let U=0,G=K.length;U<G;U++){let q=K[U],E=J(q,$);X.push(E)}Q.morphAttributes[Y]=X}Q.morphTargetsRelative=this.morphTargetsRelative;let H=this.groups;for(let Y=0,X=H.length;Y<X;Y++){let K=H[Y];Q.addGroup(K.start,K.count,K.materialIndex)}return Q}toJSON(){let J={metadata:{version:4.7,type:"BufferGeometry",generator:"BufferGeometry.toJSON"}};if(J.uuid=this.uuid,J.type=this.type,this.name!=="")J.name=this.name;if(Object.keys(this.userData).length>0)J.userData=this.userData;if(this.parameters!==void 0){let X=this.parameters;for(let K in X)if(X[K]!==void 0)J[K]=X[K];return J}J.data={attributes:{}};let Q=this.index;if(Q!==null)J.data.index={type:Q.array.constructor.name,array:Array.prototype.slice.call(Q.array)};let $=this.attributes;for(let X in $){let K=$[X];J.data.attributes[X]=K.toJSON(J.data)}let Z={},W=!1;for(let X in this.morphAttributes){let K=this.morphAttributes[X],U=[];for(let G=0,q=K.length;G<q;G++){let E=K[G];U.push(E.toJSON(J.data))}if(U.length>0)Z[X]=U,W=!0}if(W)J.data.morphAttributes=Z,J.data.morphTargetsRelative=this.morphTargetsRelative;let H=this.groups;if(H.length>0)J.data.groups=JSON.parse(JSON.stringify(H));let Y=this.boundingSphere;if(Y!==null)J.data.boundingSphere=Y.toJSON();return J}clone(){return new this.constructor().copy(this)}copy(J){this.index=null,this.attributes={},this.morphAttributes={},this.groups=[],this.boundingBox=null,this.boundingSphere=null;let Q={};this.name=J.name;let $=J.index;if($!==null)this.setIndex($.clone());let Z=J.attributes;for(let K in Z){let U=Z[K];this.setAttribute(K,U.clone(Q))}let W=J.morphAttributes;for(let K in W){let U=[],G=W[K];for(let q=0,E=G.length;q<E;q++)U.push(G[q].clone(Q));this.morphAttributes[K]=U}this.morphTargetsRelative=J.morphTargetsRelative;let H=J.groups;for(let K=0,U=H.length;K<U;K++){let G=H[K];this.addGroup(G.start,G.count,G.materialIndex)}let Y=J.boundingBox;if(Y!==null)this.boundingBox=Y.clone();let X=J.boundingSphere;if(X!==null)this.boundingSphere=X.clone();return this.drawRange.start=J.drawRange.start,this.drawRange.count=J.drawRange.count,this.userData=J.userData,this}dispose(){this.dispatchEvent({type:"dispose"})}}var DZ=new vJ,e8=new m8,x6=new x0,LZ=new A,g6=new A,p6=new A,l6=new A,FQ=new A,d6=new A,VZ=new A,m6=new A;class C0 extends Z0{constructor(J=new p0,Q=new G8){super();this.isMesh=!0,this.type="Mesh",this.geometry=J,this.material=Q,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.count=1,this.updateMorphTargets()}copy(J,Q){if(super.copy(J,Q),J.morphTargetInfluences!==void 0)this.morphTargetInfluences=J.morphTargetInfluences.slice();if(J.morphTargetDictionary!==void 0)this.morphTargetDictionary=Object.assign({},J.morphTargetDictionary);return this.material=Array.isArray(J.material)?J.material.slice():J.material,this.geometry=J.geometry,this}updateMorphTargets(){let Q=this.geometry.morphAttributes,$=Object.keys(Q);if($.length>0){let Z=Q[$[0]];if(Z!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let W=0,H=Z.length;W<H;W++){let Y=Z[W].name||String(W);this.morphTargetInfluences.push(0),this.morphTargetDictionary[Y]=W}}}}getVertexPosition(J,Q){let $=this.geometry,Z=$.attributes.position,W=$.morphAttributes.position,H=$.morphTargetsRelative;Q.fromBufferAttribute(Z,J);let Y=this.morphTargetInfluences;if(W&&Y){d6.set(0,0,0);for(let X=0,K=W.length;X<K;X++){let U=Y[X],G=W[X];if(U===0)continue;if(FQ.fromBufferAttribute(G,J),H)d6.addScaledVector(FQ,U);else d6.addScaledVector(FQ.sub(Q),U)}Q.add(d6)}return Q}raycast(J,Q){let $=this.geometry,Z=this.material,W=this.matrixWorld;if(Z===void 0)return;if($.boundingSphere===null)$.computeBoundingSphere();if(x6.copy($.boundingSphere),x6.applyMatrix4(W),e8.copy(J.ray).recast(J.near),x6.containsPoint(e8.origin)===!1){if(e8.intersectSphere(x6,LZ)===null)return;if(e8.origin.distanceToSquared(LZ)>(J.far-J.near)**2)return}if(DZ.copy(W).invert(),e8.copy(J.ray).applyMatrix4(DZ),$.boundingBox!==null){if(e8.intersectsBox($.boundingBox)===!1)return}this._computeIntersections(J,Q,e8)}_computeIntersections(J,Q,$){let Z,W=this.geometry,H=this.material,Y=W.index,X=W.attributes.position,K=W.attributes.uv,U=W.attributes.uv1,G=W.attributes.normal,q=W.groups,E=W.drawRange;if(Y!==null)if(Array.isArray(H))for(let F=0,k=q.length;F<k;F++){let M=q[F],N=H[M.materialIndex],O=Math.max(M.start,E.start),C=Math.min(Y.count,Math.min(M.start+M.count,E.start+E.count));for(let L=O,w=C;L<w;L+=3){let v=Y.getX(L),_=Y.getX(L+1),T=Y.getX(L+2);if(Z=u6(this,N,J,$,K,U,G,v,_,T),Z)Z.faceIndex=Math.floor(L/3),Z.face.materialIndex=M.materialIndex,Q.push(Z)}}else{let F=Math.max(0,E.start),k=Math.min(Y.count,E.start+E.count);for(let M=F,N=k;M<N;M+=3){let O=Y.getX(M),C=Y.getX(M+1),L=Y.getX(M+2);if(Z=u6(this,H,J,$,K,U,G,O,C,L),Z)Z.faceIndex=Math.floor(M/3),Q.push(Z)}}else if(X!==void 0)if(Array.isArray(H))for(let F=0,k=q.length;F<k;F++){let M=q[F],N=H[M.materialIndex],O=Math.max(M.start,E.start),C=Math.min(X.count,Math.min(M.start+M.count,E.start+E.count));for(let L=O,w=C;L<w;L+=3){let v=L,_=L+1,T=L+2;if(Z=u6(this,N,J,$,K,U,G,v,_,T),Z)Z.faceIndex=Math.floor(L/3),Z.face.materialIndex=M.materialIndex,Q.push(Z)}}else{let F=Math.max(0,E.start),k=Math.min(X.count,E.start+E.count);for(let M=F,N=k;M<N;M+=3){let O=M,C=M+1,L=M+2;if(Z=u6(this,H,J,$,K,U,G,O,C,L),Z)Z.faceIndex=Math.floor(M/3),Q.push(Z)}}}}function cY(J,Q,$,Z,W,H,Y,X){let K;if(Q.side===1)K=Z.intersectTriangle(Y,H,W,!0,X);else K=Z.intersectTriangle(W,H,Y,Q.side===0,X);if(K===null)return null;m6.copy(X),m6.applyMatrix4(J.matrixWorld);let U=$.ray.origin.distanceTo(m6);if(U<$.near||U>$.far)return null;return{distance:U,point:m6.clone(),object:J}}function u6(J,Q,$,Z,W,H,Y,X,K,U){J.getVertexPosition(X,g6),J.getVertexPosition(K,p6),J.getVertexPosition(U,l6);let G=cY(J,Q,$,Z,g6,p6,l6,VZ);if(G){let q=new A;if(n0.getBarycoord(VZ,g6,p6,l6,q),W)G.uv=n0.getInterpolatedAttribute(W,X,K,U,q,new PJ);if(H)G.uv1=n0.getInterpolatedAttribute(H,X,K,U,q,new PJ);if(Y){if(G.normal=n0.getInterpolatedAttribute(Y,X,K,U,q,new A),G.normal.dot(Z.direction)>0)G.normal.multiplyScalar(-1)}let E={a:X,b:K,c:U,normal:new A,materialIndex:0};n0.getNormal(g6,p6,l6,E.normal),G.face=E,G.barycoord=q}return G}class x9 extends p0{constructor(J=1,Q=1,$=1,Z=1,W=1,H=1){super();this.type="BoxGeometry",this.parameters={width:J,height:Q,depth:$,widthSegments:Z,heightSegments:W,depthSegments:H};let Y=this;Z=Math.floor(Z),W=Math.floor(W),H=Math.floor(H);let X=[],K=[],U=[],G=[],q=0,E=0;F("z","y","x",-1,-1,$,Q,J,H,W,0),F("z","y","x",1,-1,$,Q,-J,H,W,1),F("x","z","y",1,1,J,$,Q,Z,H,2),F("x","z","y",1,-1,J,$,-Q,Z,H,3),F("x","y","z",1,-1,J,Q,$,Z,W,4),F("x","y","z",-1,-1,J,Q,-$,Z,W,5),this.setIndex(X),this.setAttribute("position",new s0(K,3)),this.setAttribute("normal",new s0(U,3)),this.setAttribute("uv",new s0(G,2));function F(k,M,N,O,C,L,w,v,_,T,x){let z=L/_,V=w/T,j=L/2,m=w/2,l=v/2,c=_+1,i=T+1,u=0,r=0,g=new A;for(let ZJ=0;ZJ<i;ZJ++){let UJ=ZJ*V-m;for(let TJ=0;TJ<c;TJ++){let mJ=TJ*z-j;g[k]=mJ*O,g[M]=UJ*C,g[N]=l,K.push(g.x,g.y,g.z),g[k]=0,g[M]=0,g[N]=v>0?1:-1,U.push(g.x,g.y,g.z),G.push(TJ/_),G.push(1-ZJ/T),u+=1}}for(let ZJ=0;ZJ<T;ZJ++)for(let UJ=0;UJ<_;UJ++){let TJ=q+UJ+c*ZJ,mJ=q+UJ+c*(ZJ+1),Y0=q+(UJ+1)+c*(ZJ+1),d=q+(UJ+1)+c*ZJ;X.push(TJ,mJ,d),X.push(mJ,Y0,d),r+=6}Y.addGroup(E,r,x),E+=r,q+=u}}copy(J){return super.copy(J),this.parameters=Object.assign({},J.parameters),this}static fromJSON(J){return new x9(J.width,J.height,J.depth,J.widthSegments,J.heightSegments,J.depthSegments)}}function K9(J){let Q={};for(let $ in J){Q[$]={};for(let Z in J[$]){let W=J[$][Z];if(W&&(W.isColor||W.isMatrix3||W.isMatrix4||W.isVector2||W.isVector3||W.isVector4||W.isTexture||W.isQuaternion))if(W.isRenderTargetTexture)console.warn("UniformsUtils: Textures of render targets cannot be cloned via cloneUniforms() or mergeUniforms()."),Q[$][Z]=null;else Q[$][Z]=W.clone();else if(Array.isArray(W))Q[$][Z]=W.slice();else Q[$][Z]=W}}return Q}function w0(J){let Q={};for(let $=0;$<J.length;$++){let Z=K9(J[$]);for(let W in Z)Q[W]=Z[W]}return Q}function nY(J){let Q=[];for(let $=0;$<J.length;$++)Q.push(J[$].clone());return Q}function M$(J){let Q=J.getRenderTarget();if(Q===null)return J.outputColorSpace;if(Q.isXRRenderTarget===!0)return Q.texture.colorSpace;return lJ.workingColorSpace}var mW={clone:K9,merge:w0},sY=`void main() {
	gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );
}`,oY=`void main() {
	gl_FragColor = vec4( 1.0, 0.0, 0.0, 1.0 );
}`;class q8 extends g0{constructor(J){super();if(this.isShaderMaterial=!0,this.type="ShaderMaterial",this.defines={},this.uniforms={},this.uniformsGroups=[],this.vertexShader=sY,this.fragmentShader=oY,this.linewidth=1,this.wireframe=!1,this.wireframeLinewidth=1,this.fog=!1,this.lights=!1,this.clipping=!1,this.forceSinglePass=!0,this.extensions={clipCullDistance:!1,multiDraw:!1},this.defaultAttributeValues={color:[1,1,1],uv:[0,0],uv1:[0,0]},this.index0AttributeName=void 0,this.uniformsNeedUpdate=!1,this.glslVersion=null,J!==void 0)this.setValues(J)}copy(J){return super.copy(J),this.fragmentShader=J.fragmentShader,this.vertexShader=J.vertexShader,this.uniforms=K9(J.uniforms),this.uniformsGroups=nY(J.uniformsGroups),this.defines=Object.assign({},J.defines),this.wireframe=J.wireframe,this.wireframeLinewidth=J.wireframeLinewidth,this.fog=J.fog,this.lights=J.lights,this.clipping=J.clipping,this.extensions=Object.assign({},J.extensions),this.glslVersion=J.glslVersion,this}toJSON(J){let Q=super.toJSON(J);Q.glslVersion=this.glslVersion,Q.uniforms={};for(let Z in this.uniforms){let H=this.uniforms[Z].value;if(H&&H.isTexture)Q.uniforms[Z]={type:"t",value:H.toJSON(J).uuid};else if(H&&H.isColor)Q.uniforms[Z]={type:"c",value:H.getHex()};else if(H&&H.isVector2)Q.uniforms[Z]={type:"v2",value:H.toArray()};else if(H&&H.isVector3)Q.uniforms[Z]={type:"v3",value:H.toArray()};else if(H&&H.isVector4)Q.uniforms[Z]={type:"v4",value:H.toArray()};else if(H&&H.isMatrix3)Q.uniforms[Z]={type:"m3",value:H.toArray()};else if(H&&H.isMatrix4)Q.uniforms[Z]={type:"m4",value:H.toArray()};else Q.uniforms[Z]={value:H}}if(Object.keys(this.defines).length>0)Q.defines=this.defines;Q.vertexShader=this.vertexShader,Q.fragmentShader=this.fragmentShader,Q.lights=this.lights,Q.clipping=this.clipping;let $={};for(let Z in this.extensions)if(this.extensions[Z]===!0)$[Z]=!0;if(Object.keys($).length>0)Q.extensions=$;return Q}}class C7 extends Z0{constructor(){super();this.isCamera=!0,this.type="Camera",this.matrixWorldInverse=new vJ,this.projectionMatrix=new vJ,this.projectionMatrixInverse=new vJ,this.coordinateSystem=2000,this._reversedDepth=!1}get reversedDepth(){return this._reversedDepth}copy(J,Q){return super.copy(J,Q),this.matrixWorldInverse.copy(J.matrixWorldInverse),this.projectionMatrix.copy(J.projectionMatrix),this.projectionMatrixInverse.copy(J.projectionMatrixInverse),this.coordinateSystem=J.coordinateSystem,this}getWorldDirection(J){return super.getWorldDirection(J).negate()}updateMatrixWorld(J){super.updateMatrixWorld(J),this.matrixWorldInverse.copy(this.matrixWorld).invert()}updateWorldMatrix(J,Q){super.updateWorldMatrix(J,Q),this.matrixWorldInverse.copy(this.matrixWorld).invert()}clone(){return new this.constructor().copy(this)}}var f8=new A,zZ=new PJ,BZ=new PJ;class O0 extends C7{constructor(J=50,Q=1,$=0.1,Z=2000){super();this.isPerspectiveCamera=!0,this.type="PerspectiveCamera",this.fov=J,this.zoom=1,this.near=$,this.far=Z,this.focus=10,this.aspect=Q,this.view=null,this.filmGauge=35,this.filmOffset=0,this.updateProjectionMatrix()}copy(J,Q){return super.copy(J,Q),this.fov=J.fov,this.zoom=J.zoom,this.near=J.near,this.far=J.far,this.focus=J.focus,this.aspect=J.aspect,this.view=J.view===null?null:Object.assign({},J.view),this.filmGauge=J.filmGauge,this.filmOffset=J.filmOffset,this}setFocalLength(J){let Q=0.5*this.getFilmHeight()/J;this.fov=Q9*2*Math.atan(Q),this.updateProjectionMatrix()}getFocalLength(){let J=Math.tan(W6*0.5*this.fov);return 0.5*this.getFilmHeight()/J}getEffectiveFOV(){return Q9*2*Math.atan(Math.tan(W6*0.5*this.fov)/this.zoom)}getFilmWidth(){return this.filmGauge*Math.min(this.aspect,1)}getFilmHeight(){return this.filmGauge/Math.max(this.aspect,1)}getViewBounds(J,Q,$){f8.set(-1,-1,0.5).applyMatrix4(this.projectionMatrixInverse),Q.set(f8.x,f8.y).multiplyScalar(-J/f8.z),f8.set(1,1,0.5).applyMatrix4(this.projectionMatrixInverse),$.set(f8.x,f8.y).multiplyScalar(-J/f8.z)}getViewSize(J,Q){return this.getViewBounds(J,zZ,BZ),Q.subVectors(BZ,zZ)}setViewOffset(J,Q,$,Z,W,H){if(this.aspect=J/Q,this.view===null)this.view={enabled:!0,fullWidth:1,fullHeight:1,offsetX:0,offsetY:0,width:1,height:1};this.view.enabled=!0,this.view.fullWidth=J,this.view.fullHeight=Q,this.view.offsetX=$,this.view.offsetY=Z,this.view.width=W,this.view.height=H,this.updateProjectionMatrix()}clearViewOffset(){if(this.view!==null)this.view.enabled=!1;this.updateProjectionMatrix()}updateProjectionMatrix(){let J=this.near,Q=J*Math.tan(W6*0.5*this.fov)/this.zoom,$=2*Q,Z=this.aspect*$,W=-0.5*Z,H=this.view;if(this.view!==null&&this.view.enabled){let{fullWidth:X,fullHeight:K}=H;W+=H.offsetX*Z/X,Q-=H.offsetY*$/K,Z*=H.width/X,$*=H.height/K}let Y=this.filmOffset;if(Y!==0)W+=J*Y/this.getFilmWidth();this.projectionMatrix.makePerspective(W,W+Z,Q,Q-$,J,this.far,this.coordinateSystem,this.reversedDepth),this.projectionMatrixInverse.copy(this.projectionMatrix).invert()}toJSON(J){let Q=super.toJSON(J);if(Q.object.fov=this.fov,Q.object.zoom=this.zoom,Q.object.near=this.near,Q.object.far=this.far,Q.object.focus=this.focus,Q.object.aspect=this.aspect,this.view!==null)Q.object.view=Object.assign({},this.view);return Q.object.filmGauge=this.filmGauge,Q.object.filmOffset=this.filmOffset,Q}}var w9=-90,_9=1;class D$ extends Z0{constructor(J,Q,$){super();this.type="CubeCamera",this.renderTarget=$,this.coordinateSystem=null,this.activeMipmapLevel=0;let Z=new O0(w9,_9,J,Q);Z.layers=this.layers,this.add(Z);let W=new O0(w9,_9,J,Q);W.layers=this.layers,this.add(W);let H=new O0(w9,_9,J,Q);H.layers=this.layers,this.add(H);let Y=new O0(w9,_9,J,Q);Y.layers=this.layers,this.add(Y);let X=new O0(w9,_9,J,Q);X.layers=this.layers,this.add(X);let K=new O0(w9,_9,J,Q);K.layers=this.layers,this.add(K)}updateCoordinateSystem(){let J=this.coordinateSystem,Q=this.children.concat(),[$,Z,W,H,Y,X]=Q;for(let K of Q)this.remove(K);if(J===2000)$.up.set(0,1,0),$.lookAt(1,0,0),Z.up.set(0,1,0),Z.lookAt(-1,0,0),W.up.set(0,0,-1),W.lookAt(0,1,0),H.up.set(0,0,1),H.lookAt(0,-1,0),Y.up.set(0,1,0),Y.lookAt(0,0,1),X.up.set(0,1,0),X.lookAt(0,0,-1);else if(J===2001)$.up.set(0,-1,0),$.lookAt(-1,0,0),Z.up.set(0,-1,0),Z.lookAt(1,0,0),W.up.set(0,0,1),W.lookAt(0,1,0),H.up.set(0,0,-1),H.lookAt(0,-1,0),Y.up.set(0,-1,0),Y.lookAt(0,0,1),X.up.set(0,-1,0),X.lookAt(0,0,-1);else throw new Error("THREE.CubeCamera.updateCoordinateSystem(): Invalid coordinate system: "+J);for(let K of Q)this.add(K),K.updateMatrixWorld()}update(J,Q){if(this.parent===null)this.updateMatrixWorld();let{renderTarget:$,activeMipmapLevel:Z}=this;if(this.coordinateSystem!==J.coordinateSystem)this.coordinateSystem=J.coordinateSystem,this.updateCoordinateSystem();let[W,H,Y,X,K,U]=this.children,G=J.getRenderTarget(),q=J.getActiveCubeFace(),E=J.getActiveMipmapLevel(),F=J.xr.enabled;J.xr.enabled=!1;let k=$.texture.generateMipmaps;$.texture.generateMipmaps=!1,J.setRenderTarget($,0,Z),J.render(Q,W),J.setRenderTarget($,1,Z),J.render(Q,H),J.setRenderTarget($,2,Z),J.render(Q,Y),J.setRenderTarget($,3,Z),J.render(Q,X),J.setRenderTarget($,4,Z),J.render(Q,K),$.texture.generateMipmaps=k,J.setRenderTarget($,5,Z),J.render(Q,U),J.setRenderTarget(G,q,E),J.xr.enabled=F,$.texture.needsPMREMUpdate=!0}}class w7 extends E0{constructor(J=[],Q=301,$,Z,W,H,Y,X,K,U){super(J,Q,$,Z,W,H,Y,X,K,U);this.isCubeTexture=!0,this.flipY=!1}get images(){return this.image}set images(J){this.image=J}}class L$ extends _8{constructor(J=1,Q={}){super(J,J,Q);this.isWebGLCubeRenderTarget=!0;let $={width:J,height:J,depth:1},Z=[$,$,$,$,$,$];this.texture=new w7(Z),this._setTextureOptions(Q),this.texture.isRenderTargetTexture=!0}fromEquirectangularTexture(J,Q){this.texture.type=Q.type,this.texture.colorSpace=Q.colorSpace,this.texture.generateMipmaps=Q.generateMipmaps,this.texture.minFilter=Q.minFilter,this.texture.magFilter=Q.magFilter;let $={uniforms:{tEquirect:{value:null}},vertexShader:`

				varying vec3 vWorldDirection;

				vec3 transformDirection( in vec3 dir, in mat4 matrix ) {

					return normalize( ( matrix * vec4( dir, 0.0 ) ).xyz );

				}

				void main() {

					vWorldDirection = transformDirection( position, modelMatrix );

					#include <begin_vertex>
					#include <project_vertex>

				}
			`,fragmentShader:`

				uniform sampler2D tEquirect;

				varying vec3 vWorldDirection;

				#include <common>

				void main() {

					vec3 direction = normalize( vWorldDirection );

					vec2 sampleUV = equirectUv( direction );

					gl_FragColor = texture2D( tEquirect, sampleUV );

				}
			`},Z=new x9(5,5,5),W=new q8({name:"CubemapFromEquirect",uniforms:K9($.uniforms),vertexShader:$.vertexShader,fragmentShader:$.fragmentShader,side:1,blending:0});W.uniforms.tEquirect.value=Q;let H=new C0(Z,W),Y=Q.minFilter;if(Q.minFilter===1008)Q.minFilter=1006;return new D$(1,10,this).update(J,H),Q.minFilter=Y,H.geometry.dispose(),H.material.dispose(),this}clear(J,Q=!0,$=!0,Z=!0){let W=J.getRenderTarget();for(let H=0;H<6;H++)J.setRenderTarget(this,H),J.clear(Q,$,Z);J.setRenderTarget(W)}}class Y8 extends Z0{constructor(){super();this.isGroup=!0,this.type="Group"}}var iY={type:"move"};class O6{constructor(){this._targetRay=null,this._grip=null,this._hand=null}getHandSpace(){if(this._hand===null)this._hand=new Y8,this._hand.matrixAutoUpdate=!1,this._hand.visible=!1,this._hand.joints={},this._hand.inputState={pinching:!1};return this._hand}getTargetRaySpace(){if(this._targetRay===null)this._targetRay=new Y8,this._targetRay.matrixAutoUpdate=!1,this._targetRay.visible=!1,this._targetRay.hasLinearVelocity=!1,this._targetRay.linearVelocity=new A,this._targetRay.hasAngularVelocity=!1,this._targetRay.angularVelocity=new A;return this._targetRay}getGripSpace(){if(this._grip===null)this._grip=new Y8,this._grip.matrixAutoUpdate=!1,this._grip.visible=!1,this._grip.hasLinearVelocity=!1,this._grip.linearVelocity=new A,this._grip.hasAngularVelocity=!1,this._grip.angularVelocity=new A;return this._grip}dispatchEvent(J){if(this._targetRay!==null)this._targetRay.dispatchEvent(J);if(this._grip!==null)this._grip.dispatchEvent(J);if(this._hand!==null)this._hand.dispatchEvent(J);return this}connect(J){if(J&&J.hand){let Q=this._hand;if(Q)for(let $ of J.hand.values())this._getHandJoint(Q,$)}return this.dispatchEvent({type:"connected",data:J}),this}disconnect(J){if(this.dispatchEvent({type:"disconnected",data:J}),this._targetRay!==null)this._targetRay.visible=!1;if(this._grip!==null)this._grip.visible=!1;if(this._hand!==null)this._hand.visible=!1;return this}update(J,Q,$){let Z=null,W=null,H=null,Y=this._targetRay,X=this._grip,K=this._hand;if(J&&Q.session.visibilityState!=="visible-blurred"){if(K&&J.hand){H=!0;for(let k of J.hand.values()){let M=Q.getJointPose(k,$),N=this._getHandJoint(K,k);if(M!==null)N.matrix.fromArray(M.transform.matrix),N.matrix.decompose(N.position,N.rotation,N.scale),N.matrixWorldNeedsUpdate=!0,N.jointRadius=M.radius;N.visible=M!==null}let U=K.joints["index-finger-tip"],G=K.joints["thumb-tip"],q=U.position.distanceTo(G.position),E=0.02,F=0.005;if(K.inputState.pinching&&q>E+F)K.inputState.pinching=!1,this.dispatchEvent({type:"pinchend",handedness:J.handedness,target:this});else if(!K.inputState.pinching&&q<=E-F)K.inputState.pinching=!0,this.dispatchEvent({type:"pinchstart",handedness:J.handedness,target:this})}else if(X!==null&&J.gripSpace){if(W=Q.getPose(J.gripSpace,$),W!==null){if(X.matrix.fromArray(W.transform.matrix),X.matrix.decompose(X.position,X.rotation,X.scale),X.matrixWorldNeedsUpdate=!0,W.linearVelocity)X.hasLinearVelocity=!0,X.linearVelocity.copy(W.linearVelocity);else X.hasLinearVelocity=!1;if(W.angularVelocity)X.hasAngularVelocity=!0,X.angularVelocity.copy(W.angularVelocity);else X.hasAngularVelocity=!1}}if(Y!==null){if(Z=Q.getPose(J.targetRaySpace,$),Z===null&&W!==null)Z=W;if(Z!==null){if(Y.matrix.fromArray(Z.transform.matrix),Y.matrix.decompose(Y.position,Y.rotation,Y.scale),Y.matrixWorldNeedsUpdate=!0,Z.linearVelocity)Y.hasLinearVelocity=!0,Y.linearVelocity.copy(Z.linearVelocity);else Y.hasLinearVelocity=!1;if(Z.angularVelocity)Y.hasAngularVelocity=!0,Y.angularVelocity.copy(Z.angularVelocity);else Y.hasAngularVelocity=!1;this.dispatchEvent(iY)}}}if(Y!==null)Y.visible=Z!==null;if(X!==null)X.visible=W!==null;if(K!==null)K.visible=H!==null;return this}_getHandJoint(J,Q){if(J.joints[Q.jointName]===void 0){let $=new Y8;$.matrixAutoUpdate=!1,$.visible=!1,J.joints[Q.jointName]=$,J.add($)}return J.joints[Q.jointName]}}class _7 extends Z0{constructor(){super();if(this.isScene=!0,this.type="Scene",this.background=null,this.environment=null,this.fog=null,this.backgroundBlurriness=0,this.backgroundIntensity=1,this.backgroundRotation=new $8,this.environmentIntensity=1,this.environmentRotation=new $8,this.overrideMaterial=null,typeof __THREE_DEVTOOLS__!=="undefined")__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}copy(J,Q){if(super.copy(J,Q),J.background!==null)this.background=J.background.clone();if(J.environment!==null)this.environment=J.environment.clone();if(J.fog!==null)this.fog=J.fog.clone();if(this.backgroundBlurriness=J.backgroundBlurriness,this.backgroundIntensity=J.backgroundIntensity,this.backgroundRotation.copy(J.backgroundRotation),this.environmentIntensity=J.environmentIntensity,this.environmentRotation.copy(J.environmentRotation),J.overrideMaterial!==null)this.overrideMaterial=J.overrideMaterial.clone();return this.matrixAutoUpdate=J.matrixAutoUpdate,this}toJSON(J){let Q=super.toJSON(J);if(this.fog!==null)Q.object.fog=this.fog.toJSON();if(this.backgroundBlurriness>0)Q.object.backgroundBlurriness=this.backgroundBlurriness;if(this.backgroundIntensity!==1)Q.object.backgroundIntensity=this.backgroundIntensity;if(Q.object.backgroundRotation=this.backgroundRotation.toArray(),this.environmentIntensity!==1)Q.object.environmentIntensity=this.environmentIntensity;return Q.object.environmentRotation=this.environmentRotation.toArray(),Q}}class F6{constructor(J,Q){this.isInterleavedBuffer=!0,this.array=J,this.stride=Q,this.count=J!==void 0?J.length/Q:0,this.usage=35044,this.updateRanges=[],this.version=0,this.uuid=Q8()}onUploadCallback(){}set needsUpdate(J){if(J===!0)this.version++}setUsage(J){return this.usage=J,this}addUpdateRange(J,Q){this.updateRanges.push({start:J,count:Q})}clearUpdateRanges(){this.updateRanges.length=0}copy(J){return this.array=new J.array.constructor(J.array),this.count=J.count,this.stride=J.stride,this.usage=J.usage,this}copyAt(J,Q,$){J*=this.stride,$*=Q.stride;for(let Z=0,W=this.stride;Z<W;Z++)this.array[J+Z]=Q.array[$+Z];return this}set(J,Q=0){return this.array.set(J,Q),this}clone(J){if(J.arrayBuffers===void 0)J.arrayBuffers={};if(this.array.buffer._uuid===void 0)this.array.buffer._uuid=Q8();if(J.arrayBuffers[this.array.buffer._uuid]===void 0)J.arrayBuffers[this.array.buffer._uuid]=this.array.slice(0).buffer;let Q=new this.array.constructor(J.arrayBuffers[this.array.buffer._uuid]),$=new this.constructor(Q,this.stride);return $.setUsage(this.usage),$}onUpload(J){return this.onUploadCallback=J,this}toJSON(J){if(J.arrayBuffers===void 0)J.arrayBuffers={};if(this.array.buffer._uuid===void 0)this.array.buffer._uuid=Q8();if(J.arrayBuffers[this.array.buffer._uuid]===void 0)J.arrayBuffers[this.array.buffer._uuid]=Array.from(new Uint32Array(this.array.buffer));return{uuid:this.uuid,buffer:this.array.buffer._uuid,type:this.array.constructor.name,stride:this.stride}}}var I0=new A;class g9{constructor(J,Q,$,Z=!1){this.isInterleavedBufferAttribute=!0,this.name="",this.data=J,this.itemSize=Q,this.offset=$,this.normalized=Z}get count(){return this.data.count}get array(){return this.data.array}set needsUpdate(J){this.data.needsUpdate=J}applyMatrix4(J){for(let Q=0,$=this.data.count;Q<$;Q++)I0.fromBufferAttribute(this,Q),I0.applyMatrix4(J),this.setXYZ(Q,I0.x,I0.y,I0.z);return this}applyNormalMatrix(J){for(let Q=0,$=this.count;Q<$;Q++)I0.fromBufferAttribute(this,Q),I0.applyNormalMatrix(J),this.setXYZ(Q,I0.x,I0.y,I0.z);return this}transformDirection(J){for(let Q=0,$=this.count;Q<$;Q++)I0.fromBufferAttribute(this,Q),I0.transformDirection(J),this.setXYZ(Q,I0.x,I0.y,I0.z);return this}getComponent(J,Q){let $=this.array[J*this.data.stride+this.offset+Q];if(this.normalized)$=J8($,this.array);return $}setComponent(J,Q,$){if(this.normalized)$=aJ($,this.array);return this.data.array[J*this.data.stride+this.offset+Q]=$,this}setX(J,Q){if(this.normalized)Q=aJ(Q,this.array);return this.data.array[J*this.data.stride+this.offset]=Q,this}setY(J,Q){if(this.normalized)Q=aJ(Q,this.array);return this.data.array[J*this.data.stride+this.offset+1]=Q,this}setZ(J,Q){if(this.normalized)Q=aJ(Q,this.array);return this.data.array[J*this.data.stride+this.offset+2]=Q,this}setW(J,Q){if(this.normalized)Q=aJ(Q,this.array);return this.data.array[J*this.data.stride+this.offset+3]=Q,this}getX(J){let Q=this.data.array[J*this.data.stride+this.offset];if(this.normalized)Q=J8(Q,this.array);return Q}getY(J){let Q=this.data.array[J*this.data.stride+this.offset+1];if(this.normalized)Q=J8(Q,this.array);return Q}getZ(J){let Q=this.data.array[J*this.data.stride+this.offset+2];if(this.normalized)Q=J8(Q,this.array);return Q}getW(J){let Q=this.data.array[J*this.data.stride+this.offset+3];if(this.normalized)Q=J8(Q,this.array);return Q}setXY(J,Q,$){if(J=J*this.data.stride+this.offset,this.normalized)Q=aJ(Q,this.array),$=aJ($,this.array);return this.data.array[J+0]=Q,this.data.array[J+1]=$,this}setXYZ(J,Q,$,Z){if(J=J*this.data.stride+this.offset,this.normalized)Q=aJ(Q,this.array),$=aJ($,this.array),Z=aJ(Z,this.array);return this.data.array[J+0]=Q,this.data.array[J+1]=$,this.data.array[J+2]=Z,this}setXYZW(J,Q,$,Z,W){if(J=J*this.data.stride+this.offset,this.normalized)Q=aJ(Q,this.array),$=aJ($,this.array),Z=aJ(Z,this.array),W=aJ(W,this.array);return this.data.array[J+0]=Q,this.data.array[J+1]=$,this.data.array[J+2]=Z,this.data.array[J+3]=W,this}clone(J){if(J===void 0){console.log("THREE.InterleavedBufferAttribute.clone(): Cloning an interleaved buffer attribute will de-interleave buffer data.");let Q=[];for(let $=0;$<this.count;$++){let Z=$*this.data.stride+this.offset;for(let W=0;W<this.itemSize;W++)Q.push(this.data.array[Z+W])}return new F0(new this.array.constructor(Q),this.itemSize,this.normalized)}else{if(J.interleavedBuffers===void 0)J.interleavedBuffers={};if(J.interleavedBuffers[this.data.uuid]===void 0)J.interleavedBuffers[this.data.uuid]=this.data.clone(J);return new g9(J.interleavedBuffers[this.data.uuid],this.itemSize,this.offset,this.normalized)}}toJSON(J){if(J===void 0){console.log("THREE.InterleavedBufferAttribute.toJSON(): Serializing an interleaved buffer attribute will de-interleave buffer data.");let Q=[];for(let $=0;$<this.count;$++){let Z=$*this.data.stride+this.offset;for(let W=0;W<this.itemSize;W++)Q.push(this.data.array[Z+W])}return{itemSize:this.itemSize,type:this.array.constructor.name,array:Q,normalized:this.normalized}}else{if(J.interleavedBuffers===void 0)J.interleavedBuffers={};if(J.interleavedBuffers[this.data.uuid]===void 0)J.interleavedBuffers[this.data.uuid]=this.data.toJSON(J);return{isInterleavedBufferAttribute:!0,itemSize:this.itemSize,data:this.data.uuid,offset:this.offset,normalized:this.normalized}}}}var CZ=new A,wZ=new sJ,_Z=new sJ,aY=new A,IZ=new vJ,c6=new A,RQ=new x0,PZ=new vJ,kQ=new m8;class I7 extends C0{constructor(J,Q){super(J,Q);this.isSkinnedMesh=!0,this.type="SkinnedMesh",this.bindMode="attached",this.bindMatrix=new vJ,this.bindMatrixInverse=new vJ,this.boundingBox=null,this.boundingSphere=null}computeBoundingBox(){let J=this.geometry;if(this.boundingBox===null)this.boundingBox=new S0;this.boundingBox.makeEmpty();let Q=J.getAttribute("position");for(let $=0;$<Q.count;$++)this.getVertexPosition($,c6),this.boundingBox.expandByPoint(c6)}computeBoundingSphere(){let J=this.geometry;if(this.boundingSphere===null)this.boundingSphere=new x0;this.boundingSphere.makeEmpty();let Q=J.getAttribute("position");for(let $=0;$<Q.count;$++)this.getVertexPosition($,c6),this.boundingSphere.expandByPoint(c6)}copy(J,Q){if(super.copy(J,Q),this.bindMode=J.bindMode,this.bindMatrix.copy(J.bindMatrix),this.bindMatrixInverse.copy(J.bindMatrixInverse),this.skeleton=J.skeleton,J.boundingBox!==null)this.boundingBox=J.boundingBox.clone();if(J.boundingSphere!==null)this.boundingSphere=J.boundingSphere.clone();return this}raycast(J,Q){let $=this.material,Z=this.matrixWorld;if($===void 0)return;if(this.boundingSphere===null)this.computeBoundingSphere();if(RQ.copy(this.boundingSphere),RQ.applyMatrix4(Z),J.ray.intersectsSphere(RQ)===!1)return;if(PZ.copy(Z).invert(),kQ.copy(J.ray).applyMatrix4(PZ),this.boundingBox!==null){if(kQ.intersectsBox(this.boundingBox)===!1)return}this._computeIntersections(J,Q,kQ)}getVertexPosition(J,Q){return super.getVertexPosition(J,Q),this.applyBoneTransform(J,Q),Q}bind(J,Q){if(this.skeleton=J,Q===void 0)this.updateMatrixWorld(!0),this.skeleton.calculateInverses(),Q=this.matrixWorld;this.bindMatrix.copy(Q),this.bindMatrixInverse.copy(Q).invert()}pose(){this.skeleton.pose()}normalizeSkinWeights(){let J=new sJ,Q=this.geometry.attributes.skinWeight;for(let $=0,Z=Q.count;$<Z;$++){J.fromBufferAttribute(Q,$);let W=1/J.manhattanLength();if(W!==1/0)J.multiplyScalar(W);else J.set(1,0,0,0);Q.setXYZW($,J.x,J.y,J.z,J.w)}}updateMatrixWorld(J){if(super.updateMatrixWorld(J),this.bindMode==="attached")this.bindMatrixInverse.copy(this.matrixWorld).invert();else if(this.bindMode==="detached")this.bindMatrixInverse.copy(this.bindMatrix).invert();else console.warn("THREE.SkinnedMesh: Unrecognized bindMode: "+this.bindMode)}applyBoneTransform(J,Q){let $=this.skeleton,Z=this.geometry;wZ.fromBufferAttribute(Z.attributes.skinIndex,J),_Z.fromBufferAttribute(Z.attributes.skinWeight,J),CZ.copy(Q).applyMatrix4(this.bindMatrix),Q.set(0,0,0);for(let W=0;W<4;W++){let H=_Z.getComponent(W);if(H!==0){let Y=wZ.getComponent(W);IZ.multiplyMatrices($.bones[Y].matrixWorld,$.boneInverses[Y]),Q.addScaledVector(aY.copy(CZ).applyMatrix4(IZ),H)}}return Q.applyMatrix4(this.bindMatrixInverse)}}class R6 extends Z0{constructor(){super();this.isBone=!0,this.type="Bone"}}class P7 extends E0{constructor(J=null,Q=1,$=1,Z,W,H,Y,X,K=1003,U=1003,G,q){super(null,H,Y,X,K,U,Z,W,G,q);this.isDataTexture=!0,this.image={data:J,width:Q,height:$},this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1}}var TZ=new vJ,rY=new vJ;class k6{constructor(J=[],Q=[]){this.uuid=Q8(),this.bones=J.slice(0),this.boneInverses=Q,this.boneMatrices=null,this.boneTexture=null,this.init()}init(){let J=this.bones,Q=this.boneInverses;if(this.boneMatrices=new Float32Array(J.length*16),Q.length===0)this.calculateInverses();else if(J.length!==Q.length){console.warn("THREE.Skeleton: Number of inverse bone matrices does not match amount of bones."),this.boneInverses=[];for(let $=0,Z=this.bones.length;$<Z;$++)this.boneInverses.push(new vJ)}}calculateInverses(){this.boneInverses.length=0;for(let J=0,Q=this.bones.length;J<Q;J++){let $=new vJ;if(this.bones[J])$.copy(this.bones[J].matrixWorld).invert();this.boneInverses.push($)}}pose(){for(let J=0,Q=this.bones.length;J<Q;J++){let $=this.bones[J];if($)$.matrixWorld.copy(this.boneInverses[J]).invert()}for(let J=0,Q=this.bones.length;J<Q;J++){let $=this.bones[J];if($){if($.parent&&$.parent.isBone)$.matrix.copy($.parent.matrixWorld).invert(),$.matrix.multiply($.matrixWorld);else $.matrix.copy($.matrixWorld);$.matrix.decompose($.position,$.quaternion,$.scale)}}}update(){let J=this.bones,Q=this.boneInverses,$=this.boneMatrices,Z=this.boneTexture;for(let W=0,H=J.length;W<H;W++){let Y=J[W]?J[W].matrixWorld:rY;TZ.multiplyMatrices(Y,Q[W]),TZ.toArray($,W*16)}if(Z!==null)Z.needsUpdate=!0}clone(){return new k6(this.bones,this.boneInverses)}computeBoneTexture(){let J=Math.sqrt(this.bones.length*4);J=Math.ceil(J/4)*4,J=Math.max(J,4);let Q=new Float32Array(J*J*4);Q.set(this.boneMatrices);let $=new P7(Q,J,J,1023,1015);return $.needsUpdate=!0,this.boneMatrices=Q,this.boneTexture=$,this}getBoneByName(J){for(let Q=0,$=this.bones.length;Q<$;Q++){let Z=this.bones[Q];if(Z.name===J)return Z}return}dispose(){if(this.boneTexture!==null)this.boneTexture.dispose(),this.boneTexture=null}fromJSON(J,Q){this.uuid=J.uuid;for(let $=0,Z=J.bones.length;$<Z;$++){let W=J.bones[$],H=Q[W];if(H===void 0)console.warn("THREE.Skeleton: No bone found with UUID:",W),H=new R6;this.bones.push(H),this.boneInverses.push(new vJ().fromArray(J.boneInverses[$]))}return this.init(),this}toJSON(){let J={metadata:{version:4.7,type:"Skeleton",generator:"Skeleton.toJSON"},bones:[],boneInverses:[]};J.uuid=this.uuid;let Q=this.bones,$=this.boneInverses;for(let Z=0,W=Q.length;Z<W;Z++){let H=Q[Z];J.bones.push(H.uuid);let Y=$[Z];J.boneInverses.push(Y.toArray())}return J}}class Z9 extends F0{constructor(J,Q,$,Z=1){super(J,Q,$);this.isInstancedBufferAttribute=!0,this.meshPerAttribute=Z}copy(J){return super.copy(J),this.meshPerAttribute=J.meshPerAttribute,this}toJSON(){let J=super.toJSON();return J.meshPerAttribute=this.meshPerAttribute,J.isInstancedBufferAttribute=!0,J}}var I9=new vJ,AZ=new vJ,n6=[],SZ=new S0,tY=new vJ,J6=new C0,Q6=new x0;class T7 extends C0{constructor(J,Q,$){super(J,Q);this.isInstancedMesh=!0,this.instanceMatrix=new Z9(new Float32Array($*16),16),this.instanceColor=null,this.morphTexture=null,this.count=$,this.boundingBox=null,this.boundingSphere=null;for(let Z=0;Z<$;Z++)this.setMatrixAt(Z,tY)}computeBoundingBox(){let J=this.geometry,Q=this.count;if(this.boundingBox===null)this.boundingBox=new S0;if(J.boundingBox===null)J.computeBoundingBox();this.boundingBox.makeEmpty();for(let $=0;$<Q;$++)this.getMatrixAt($,I9),SZ.copy(J.boundingBox).applyMatrix4(I9),this.boundingBox.union(SZ)}computeBoundingSphere(){let J=this.geometry,Q=this.count;if(this.boundingSphere===null)this.boundingSphere=new x0;if(J.boundingSphere===null)J.computeBoundingSphere();this.boundingSphere.makeEmpty();for(let $=0;$<Q;$++)this.getMatrixAt($,I9),Q6.copy(J.boundingSphere).applyMatrix4(I9),this.boundingSphere.union(Q6)}copy(J,Q){if(super.copy(J,Q),this.instanceMatrix.copy(J.instanceMatrix),J.morphTexture!==null)this.morphTexture=J.morphTexture.clone();if(J.instanceColor!==null)this.instanceColor=J.instanceColor.clone();if(this.count=J.count,J.boundingBox!==null)this.boundingBox=J.boundingBox.clone();if(J.boundingSphere!==null)this.boundingSphere=J.boundingSphere.clone();return this}getColorAt(J,Q){Q.fromArray(this.instanceColor.array,J*3)}getMatrixAt(J,Q){Q.fromArray(this.instanceMatrix.array,J*16)}getMorphAt(J,Q){let $=Q.morphTargetInfluences,Z=this.morphTexture.source.data.data,W=$.length+1,H=J*W+1;for(let Y=0;Y<$.length;Y++)$[Y]=Z[H+Y]}raycast(J,Q){let $=this.matrixWorld,Z=this.count;if(J6.geometry=this.geometry,J6.material=this.material,J6.material===void 0)return;if(this.boundingSphere===null)this.computeBoundingSphere();if(Q6.copy(this.boundingSphere),Q6.applyMatrix4($),J.ray.intersectsSphere(Q6)===!1)return;for(let W=0;W<Z;W++){this.getMatrixAt(W,I9),AZ.multiplyMatrices($,I9),J6.matrixWorld=AZ,J6.raycast(J,n6);for(let H=0,Y=n6.length;H<Y;H++){let X=n6[H];X.instanceId=W,X.object=this,Q.push(X)}n6.length=0}}setColorAt(J,Q){if(this.instanceColor===null)this.instanceColor=new Z9(new Float32Array(this.instanceMatrix.count*3).fill(1),3);Q.toArray(this.instanceColor.array,J*3)}setMatrixAt(J,Q){Q.toArray(this.instanceMatrix.array,J*16)}setMorphAt(J,Q){let $=Q.morphTargetInfluences,Z=$.length+1;if(this.morphTexture===null)this.morphTexture=new P7(new Float32Array(Z*this.count),Z,this.count,1028,1015);let W=this.morphTexture.source.data.data,H=0;for(let K=0;K<$.length;K++)H+=$[K];let Y=this.geometry.morphTargetsRelative?1:1-H,X=Z*J;W[X]=Y,W.set($,X+1)}updateMorphTargets(){}dispose(){if(this.dispatchEvent({type:"dispose"}),this.morphTexture!==null)this.morphTexture.dispose(),this.morphTexture=null}}var MQ=new A,eY=new A,JX=new fJ;class e0{constructor(J=new A(1,0,0),Q=0){this.isPlane=!0,this.normal=J,this.constant=Q}set(J,Q){return this.normal.copy(J),this.constant=Q,this}setComponents(J,Q,$,Z){return this.normal.set(J,Q,$),this.constant=Z,this}setFromNormalAndCoplanarPoint(J,Q){return this.normal.copy(J),this.constant=-Q.dot(this.normal),this}setFromCoplanarPoints(J,Q,$){let Z=MQ.subVectors($,Q).cross(eY.subVectors(J,Q)).normalize();return this.setFromNormalAndCoplanarPoint(Z,J),this}copy(J){return this.normal.copy(J.normal),this.constant=J.constant,this}normalize(){let J=1/this.normal.length();return this.normal.multiplyScalar(J),this.constant*=J,this}negate(){return this.constant*=-1,this.normal.negate(),this}distanceToPoint(J){return this.normal.dot(J)+this.constant}distanceToSphere(J){return this.distanceToPoint(J.center)-J.radius}projectPoint(J,Q){return Q.copy(J).addScaledVector(this.normal,-this.distanceToPoint(J))}intersectLine(J,Q){let $=J.delta(MQ),Z=this.normal.dot($);if(Z===0){if(this.distanceToPoint(J.start)===0)return Q.copy(J.start);return null}let W=-(J.start.dot(this.normal)+this.constant)/Z;if(W<0||W>1)return null;return Q.copy(J.start).addScaledVector($,W)}intersectsLine(J){let Q=this.distanceToPoint(J.start),$=this.distanceToPoint(J.end);return Q<0&&$>0||$<0&&Q>0}intersectsBox(J){return J.intersectsPlane(this)}intersectsSphere(J){return J.intersectsPlane(this)}coplanarPoint(J){return J.copy(this.normal).multiplyScalar(-this.constant)}applyMatrix4(J,Q){let $=Q||JX.getNormalMatrix(J),Z=this.coplanarPoint(MQ).applyMatrix4(J),W=this.normal.applyMatrix3($).normalize();return this.constant=-Z.dot(W),this}translate(J){return this.constant-=J.dot(this.normal),this}equals(J){return J.normal.equals(this.normal)&&J.constant===this.constant}clone(){return new this.constructor().copy(this)}}var J9=new x0,QX=new PJ(0.5,0.5),s6=new A;class M6{constructor(J=new e0,Q=new e0,$=new e0,Z=new e0,W=new e0,H=new e0){this.planes=[J,Q,$,Z,W,H]}set(J,Q,$,Z,W,H){let Y=this.planes;return Y[0].copy(J),Y[1].copy(Q),Y[2].copy($),Y[3].copy(Z),Y[4].copy(W),Y[5].copy(H),this}copy(J){let Q=this.planes;for(let $=0;$<6;$++)Q[$].copy(J.planes[$]);return this}setFromProjectionMatrix(J,Q=2000,$=!1){let Z=this.planes,W=J.elements,H=W[0],Y=W[1],X=W[2],K=W[3],U=W[4],G=W[5],q=W[6],E=W[7],F=W[8],k=W[9],M=W[10],N=W[11],O=W[12],C=W[13],L=W[14],w=W[15];if(Z[0].setComponents(K-H,E-U,N-F,w-O).normalize(),Z[1].setComponents(K+H,E+U,N+F,w+O).normalize(),Z[2].setComponents(K+Y,E+G,N+k,w+C).normalize(),Z[3].setComponents(K-Y,E-G,N-k,w-C).normalize(),$)Z[4].setComponents(X,q,M,L).normalize(),Z[5].setComponents(K-X,E-q,N-M,w-L).normalize();else if(Z[4].setComponents(K-X,E-q,N-M,w-L).normalize(),Q===2000)Z[5].setComponents(K+X,E+q,N+M,w+L).normalize();else if(Q===2001)Z[5].setComponents(X,q,M,L).normalize();else throw new Error("THREE.Frustum.setFromProjectionMatrix(): Invalid coordinate system: "+Q);return this}intersectsObject(J){if(J.boundingSphere!==void 0){if(J.boundingSphere===null)J.computeBoundingSphere();J9.copy(J.boundingSphere).applyMatrix4(J.matrixWorld)}else{let Q=J.geometry;if(Q.boundingSphere===null)Q.computeBoundingSphere();J9.copy(Q.boundingSphere).applyMatrix4(J.matrixWorld)}return this.intersectsSphere(J9)}intersectsSprite(J){J9.center.set(0,0,0);let Q=QX.distanceTo(J.center);return J9.radius=0.7071067811865476+Q,J9.applyMatrix4(J.matrixWorld),this.intersectsSphere(J9)}intersectsSphere(J){let Q=this.planes,$=J.center,Z=-J.radius;for(let W=0;W<6;W++)if(Q[W].distanceToPoint($)<Z)return!1;return!0}intersectsBox(J){let Q=this.planes;for(let $=0;$<6;$++){let Z=Q[$];if(s6.x=Z.normal.x>0?J.max.x:J.min.x,s6.y=Z.normal.y>0?J.max.y:J.min.y,s6.z=Z.normal.z>0?J.max.z:J.min.z,Z.distanceToPoint(s6)<0)return!1}return!0}containsPoint(J){let Q=this.planes;for(let $=0;$<6;$++)if(Q[$].distanceToPoint(J)<0)return!1;return!0}clone(){return new this.constructor().copy(this)}}class D6 extends g0{constructor(J){super();this.isLineBasicMaterial=!0,this.type="LineBasicMaterial",this.color=new jJ(16777215),this.map=null,this.linewidth=1,this.linecap="round",this.linejoin="round",this.fog=!0,this.setValues(J)}copy(J){return super.copy(J),this.color.copy(J.color),this.map=J.map,this.linewidth=J.linewidth,this.linecap=J.linecap,this.linejoin=J.linejoin,this.fog=J.fog,this}}var e6=new A,J7=new A,jZ=new vJ,$6=new m8,o6=new x0,DQ=new A,yZ=new A;class p9 extends Z0{constructor(J=new p0,Q=new D6){super();this.isLine=!0,this.type="Line",this.geometry=J,this.material=Q,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.updateMorphTargets()}copy(J,Q){return super.copy(J,Q),this.material=Array.isArray(J.material)?J.material.slice():J.material,this.geometry=J.geometry,this}computeLineDistances(){let J=this.geometry;if(J.index===null){let Q=J.attributes.position,$=[0];for(let Z=1,W=Q.count;Z<W;Z++)e6.fromBufferAttribute(Q,Z-1),J7.fromBufferAttribute(Q,Z),$[Z]=$[Z-1],$[Z]+=e6.distanceTo(J7);J.setAttribute("lineDistance",new s0($,1))}else console.warn("THREE.Line.computeLineDistances(): Computation only possible with non-indexed BufferGeometry.");return this}raycast(J,Q){let $=this.geometry,Z=this.matrixWorld,W=J.params.Line.threshold,H=$.drawRange;if($.boundingSphere===null)$.computeBoundingSphere();if(o6.copy($.boundingSphere),o6.applyMatrix4(Z),o6.radius+=W,J.ray.intersectsSphere(o6)===!1)return;jZ.copy(Z).invert(),$6.copy(J.ray).applyMatrix4(jZ);let Y=W/((this.scale.x+this.scale.y+this.scale.z)/3),X=Y*Y,K=this.isLineSegments?2:1,U=$.index,q=$.attributes.position;if(U!==null){let E=Math.max(0,H.start),F=Math.min(U.count,H.start+H.count);for(let k=E,M=F-1;k<M;k+=K){let N=U.getX(k),O=U.getX(k+1),C=i6(this,J,$6,X,N,O,k);if(C)Q.push(C)}if(this.isLineLoop){let k=U.getX(F-1),M=U.getX(E),N=i6(this,J,$6,X,k,M,F-1);if(N)Q.push(N)}}else{let E=Math.max(0,H.start),F=Math.min(q.count,H.start+H.count);for(let k=E,M=F-1;k<M;k+=K){let N=i6(this,J,$6,X,k,k+1,k);if(N)Q.push(N)}if(this.isLineLoop){let k=i6(this,J,$6,X,F-1,E,F-1);if(k)Q.push(k)}}}updateMorphTargets(){let Q=this.geometry.morphAttributes,$=Object.keys(Q);if($.length>0){let Z=Q[$[0]];if(Z!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let W=0,H=Z.length;W<H;W++){let Y=Z[W].name||String(W);this.morphTargetInfluences.push(0),this.morphTargetDictionary[Y]=W}}}}}function i6(J,Q,$,Z,W,H,Y){let X=J.geometry.attributes.position;if(e6.fromBufferAttribute(X,W),J7.fromBufferAttribute(X,H),$.distanceSqToSegment(e6,J7,DQ,yZ)>Z)return;DQ.applyMatrix4(J.matrixWorld);let U=Q.ray.origin.distanceTo(DQ);if(U<Q.near||U>Q.far)return;return{distance:U,point:yZ.clone().applyMatrix4(J.matrixWorld),index:Y,face:null,faceIndex:null,barycoord:null,object:J}}var vZ=new A,fZ=new A;class A7 extends p9{constructor(J,Q){super(J,Q);this.isLineSegments=!0,this.type="LineSegments"}computeLineDistances(){let J=this.geometry;if(J.index===null){let Q=J.attributes.position,$=[];for(let Z=0,W=Q.count;Z<W;Z+=2)vZ.fromBufferAttribute(Q,Z),fZ.fromBufferAttribute(Q,Z+1),$[Z]=Z===0?0:$[Z-1],$[Z+1]=$[Z]+vZ.distanceTo(fZ);J.setAttribute("lineDistance",new s0($,1))}else console.warn("THREE.LineSegments.computeLineDistances(): Computation only possible with non-indexed BufferGeometry.");return this}}class S7 extends p9{constructor(J,Q){super(J,Q);this.isLineLoop=!0,this.type="LineLoop"}}class L6 extends g0{constructor(J){super();this.isPointsMaterial=!0,this.type="PointsMaterial",this.color=new jJ(16777215),this.map=null,this.alphaMap=null,this.size=1,this.sizeAttenuation=!0,this.fog=!0,this.setValues(J)}copy(J){return super.copy(J),this.color.copy(J.color),this.map=J.map,this.alphaMap=J.alphaMap,this.size=J.size,this.sizeAttenuation=J.sizeAttenuation,this.fog=J.fog,this}}var hZ=new vJ,BQ=new m8,a6=new x0,r6=new A;class j7 extends Z0{constructor(J=new p0,Q=new L6){super();this.isPoints=!0,this.type="Points",this.geometry=J,this.material=Q,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.updateMorphTargets()}copy(J,Q){return super.copy(J,Q),this.material=Array.isArray(J.material)?J.material.slice():J.material,this.geometry=J.geometry,this}raycast(J,Q){let $=this.geometry,Z=this.matrixWorld,W=J.params.Points.threshold,H=$.drawRange;if($.boundingSphere===null)$.computeBoundingSphere();if(a6.copy($.boundingSphere),a6.applyMatrix4(Z),a6.radius+=W,J.ray.intersectsSphere(a6)===!1)return;hZ.copy(Z).invert(),BQ.copy(J.ray).applyMatrix4(hZ);let Y=W/((this.scale.x+this.scale.y+this.scale.z)/3),X=Y*Y,K=$.index,G=$.attributes.position;if(K!==null){let q=Math.max(0,H.start),E=Math.min(K.count,H.start+H.count);for(let F=q,k=E;F<k;F++){let M=K.getX(F);r6.fromBufferAttribute(G,M),bZ(r6,M,X,Z,J,Q,this)}}else{let q=Math.max(0,H.start),E=Math.min(G.count,H.start+H.count);for(let F=q,k=E;F<k;F++)r6.fromBufferAttribute(G,F),bZ(r6,F,X,Z,J,Q,this)}}updateMorphTargets(){let Q=this.geometry.morphAttributes,$=Object.keys(Q);if($.length>0){let Z=Q[$[0]];if(Z!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let W=0,H=Z.length;W<H;W++){let Y=Z[W].name||String(W);this.morphTargetInfluences.push(0),this.morphTargetDictionary[Y]=W}}}}}function bZ(J,Q,$,Z,W,H,Y){let X=BQ.distanceSqToPoint(J);if(X<$){let K=new A;BQ.closestPointToPoint(J,K),K.applyMatrix4(Z);let U=W.ray.origin.distanceTo(K);if(U<W.near||U>W.far)return;H.push({distance:U,distanceToRay:Math.sqrt(X),point:K,index:Q,face:null,faceIndex:null,barycoord:null,object:Y})}}class y7 extends E0{constructor(J,Q,$=1014,Z,W,H,Y=1003,X=1003,K,U=1026,G=1){if(U!==1026&&U!==1027)throw new Error("DepthTexture format must be either THREE.DepthFormat or THREE.DepthStencilFormat");let q={width:J,height:Q,depth:G};super(q,Z,W,H,Y,X,U,$,K);this.isDepthTexture=!0,this.flipY=!1,this.generateMipmaps=!1,this.compareFunction=null}copy(J){return super.copy(J),this.source=new N6(Object.assign({},J.image)),this.compareFunction=J.compareFunction,this}toJSON(J){let Q=super.toJSON(J);if(this.compareFunction!==null)Q.compareFunction=this.compareFunction;return Q}}class V6 extends p0{constructor(J=1,Q=1,$=1,Z=1){super();this.type="PlaneGeometry",this.parameters={width:J,height:Q,widthSegments:$,heightSegments:Z};let W=J/2,H=Q/2,Y=Math.floor($),X=Math.floor(Z),K=Y+1,U=X+1,G=J/Y,q=Q/X,E=[],F=[],k=[],M=[];for(let N=0;N<U;N++){let O=N*q-H;for(let C=0;C<K;C++){let L=C*G-W;F.push(L,-O,0),k.push(0,0,1),M.push(C/Y),M.push(1-N/X)}}for(let N=0;N<X;N++)for(let O=0;O<Y;O++){let C=O+K*N,L=O+K*(N+1),w=O+1+K*(N+1),v=O+1+K*N;E.push(C,L,v),E.push(L,w,v)}this.setIndex(E),this.setAttribute("position",new s0(F,3)),this.setAttribute("normal",new s0(k,3)),this.setAttribute("uv",new s0(M,2))}copy(J){return super.copy(J),this.parameters=Object.assign({},J.parameters),this}static fromJSON(J){return new V6(J.width,J.height,J.widthSegments,J.heightSegments)}}class l9 extends g0{constructor(J){super();this.isMeshStandardMaterial=!0,this.type="MeshStandardMaterial",this.defines={STANDARD:""},this.color=new jJ(16777215),this.roughness=1,this.metalness=0,this.map=null,this.lightMap=null,this.lightMapIntensity=1,this.aoMap=null,this.aoMapIntensity=1,this.emissive=new jJ(0),this.emissiveIntensity=1,this.emissiveMap=null,this.bumpMap=null,this.bumpScale=1,this.normalMap=null,this.normalMapType=0,this.normalScale=new PJ(1,1),this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.roughnessMap=null,this.metalnessMap=null,this.alphaMap=null,this.envMap=null,this.envMapRotation=new $8,this.envMapIntensity=1,this.wireframe=!1,this.wireframeLinewidth=1,this.wireframeLinecap="round",this.wireframeLinejoin="round",this.flatShading=!1,this.fog=!0,this.setValues(J)}copy(J){return super.copy(J),this.defines={STANDARD:""},this.color.copy(J.color),this.roughness=J.roughness,this.metalness=J.metalness,this.map=J.map,this.lightMap=J.lightMap,this.lightMapIntensity=J.lightMapIntensity,this.aoMap=J.aoMap,this.aoMapIntensity=J.aoMapIntensity,this.emissive.copy(J.emissive),this.emissiveMap=J.emissiveMap,this.emissiveIntensity=J.emissiveIntensity,this.bumpMap=J.bumpMap,this.bumpScale=J.bumpScale,this.normalMap=J.normalMap,this.normalMapType=J.normalMapType,this.normalScale.copy(J.normalScale),this.displacementMap=J.displacementMap,this.displacementScale=J.displacementScale,this.displacementBias=J.displacementBias,this.roughnessMap=J.roughnessMap,this.metalnessMap=J.metalnessMap,this.alphaMap=J.alphaMap,this.envMap=J.envMap,this.envMapRotation.copy(J.envMapRotation),this.envMapIntensity=J.envMapIntensity,this.wireframe=J.wireframe,this.wireframeLinewidth=J.wireframeLinewidth,this.wireframeLinecap=J.wireframeLinecap,this.wireframeLinejoin=J.wireframeLinejoin,this.flatShading=J.flatShading,this.fog=J.fog,this}}class l0 extends l9{constructor(J){super();this.isMeshPhysicalMaterial=!0,this.defines={STANDARD:"",PHYSICAL:""},this.type="MeshPhysicalMaterial",this.anisotropyRotation=0,this.anisotropyMap=null,this.clearcoatMap=null,this.clearcoatRoughness=0,this.clearcoatRoughnessMap=null,this.clearcoatNormalScale=new PJ(1,1),this.clearcoatNormalMap=null,this.ior=1.5,Object.defineProperty(this,"reflectivity",{get:function(){return xJ(2.5*(this.ior-1)/(this.ior+1),0,1)},set:function(Q){this.ior=(1+0.4*Q)/(1-0.4*Q)}}),this.iridescenceMap=null,this.iridescenceIOR=1.3,this.iridescenceThicknessRange=[100,400],this.iridescenceThicknessMap=null,this.sheenColor=new jJ(0),this.sheenColorMap=null,this.sheenRoughness=1,this.sheenRoughnessMap=null,this.transmissionMap=null,this.thickness=0,this.thicknessMap=null,this.attenuationDistance=1/0,this.attenuationColor=new jJ(1,1,1),this.specularIntensity=1,this.specularIntensityMap=null,this.specularColor=new jJ(1,1,1),this.specularColorMap=null,this._anisotropy=0,this._clearcoat=0,this._dispersion=0,this._iridescence=0,this._sheen=0,this._transmission=0,this.setValues(J)}get anisotropy(){return this._anisotropy}set anisotropy(J){if(this._anisotropy>0!==J>0)this.version++;this._anisotropy=J}get clearcoat(){return this._clearcoat}set clearcoat(J){if(this._clearcoat>0!==J>0)this.version++;this._clearcoat=J}get iridescence(){return this._iridescence}set iridescence(J){if(this._iridescence>0!==J>0)this.version++;this._iridescence=J}get dispersion(){return this._dispersion}set dispersion(J){if(this._dispersion>0!==J>0)this.version++;this._dispersion=J}get sheen(){return this._sheen}set sheen(J){if(this._sheen>0!==J>0)this.version++;this._sheen=J}get transmission(){return this._transmission}set transmission(J){if(this._transmission>0!==J>0)this.version++;this._transmission=J}copy(J){return super.copy(J),this.defines={STANDARD:"",PHYSICAL:""},this.anisotropy=J.anisotropy,this.anisotropyRotation=J.anisotropyRotation,this.anisotropyMap=J.anisotropyMap,this.clearcoat=J.clearcoat,this.clearcoatMap=J.clearcoatMap,this.clearcoatRoughness=J.clearcoatRoughness,this.clearcoatRoughnessMap=J.clearcoatRoughnessMap,this.clearcoatNormalMap=J.clearcoatNormalMap,this.clearcoatNormalScale.copy(J.clearcoatNormalScale),this.dispersion=J.dispersion,this.ior=J.ior,this.iridescence=J.iridescence,this.iridescenceMap=J.iridescenceMap,this.iridescenceIOR=J.iridescenceIOR,this.iridescenceThicknessRange=[...J.iridescenceThicknessRange],this.iridescenceThicknessMap=J.iridescenceThicknessMap,this.sheen=J.sheen,this.sheenColor.copy(J.sheenColor),this.sheenColorMap=J.sheenColorMap,this.sheenRoughness=J.sheenRoughness,this.sheenRoughnessMap=J.sheenRoughnessMap,this.transmission=J.transmission,this.transmissionMap=J.transmissionMap,this.thickness=J.thickness,this.thicknessMap=J.thicknessMap,this.attenuationDistance=J.attenuationDistance,this.attenuationColor.copy(J.attenuationColor),this.specularIntensity=J.specularIntensity,this.specularIntensityMap=J.specularIntensityMap,this.specularColor.copy(J.specularColor),this.specularColorMap=J.specularColorMap,this}}class V$ extends g0{constructor(J){super();this.isMeshDepthMaterial=!0,this.type="MeshDepthMaterial",this.depthPacking=3200,this.map=null,this.alphaMap=null,this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.wireframe=!1,this.wireframeLinewidth=1,this.setValues(J)}copy(J){return super.copy(J),this.depthPacking=J.depthPacking,this.map=J.map,this.alphaMap=J.alphaMap,this.displacementMap=J.displacementMap,this.displacementScale=J.displacementScale,this.displacementBias=J.displacementBias,this.wireframe=J.wireframe,this.wireframeLinewidth=J.wireframeLinewidth,this}}class z$ extends g0{constructor(J){super();this.isMeshDistanceMaterial=!0,this.type="MeshDistanceMaterial",this.map=null,this.alphaMap=null,this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.setValues(J)}copy(J){return super.copy(J),this.map=J.map,this.alphaMap=J.alphaMap,this.displacementMap=J.displacementMap,this.displacementScale=J.displacementScale,this.displacementBias=J.displacementBias,this}}function t6(J,Q){if(!J||J.constructor===Q)return J;if(typeof Q.BYTES_PER_ELEMENT==="number")return new Q(J);return Array.prototype.slice.call(J)}function $X(J){return ArrayBuffer.isView(J)&&!(J instanceof DataView)}function ZX(J){function Q(W,H){return J[W]-J[H]}let $=J.length,Z=new Array($);for(let W=0;W!==$;++W)Z[W]=W;return Z.sort(Q),Z}function xZ(J,Q,$){let Z=J.length,W=new J.constructor(Z);for(let H=0,Y=0;Y!==Z;++H){let X=$[H]*Q;for(let K=0;K!==Q;++K)W[Y++]=J[X+K]}return W}function uW(J,Q,$,Z){let W=1,H=J[0];while(H!==void 0&&H[Z]===void 0)H=J[W++];if(H===void 0)return;let Y=H[Z];if(Y===void 0)return;if(Array.isArray(Y))do{if(Y=H[Z],Y!==void 0)Q.push(H.time),$.push(...Y);H=J[W++]}while(H!==void 0);else if(Y.toArray!==void 0)do{if(Y=H[Z],Y!==void 0)Q.push(H.time),Y.toArray($,$.length);H=J[W++]}while(H!==void 0);else do{if(Y=H[Z],Y!==void 0)Q.push(H.time),$.push(Y);H=J[W++]}while(H!==void 0)}class u8{constructor(J,Q,$,Z){this.parameterPositions=J,this._cachedIndex=0,this.resultBuffer=Z!==void 0?Z:new Q.constructor($),this.sampleValues=Q,this.valueSize=$,this.settings=null,this.DefaultSettings_={}}evaluate(J){let Q=this.parameterPositions,$=this._cachedIndex,Z=Q[$],W=Q[$-1];$:{J:{let H;Q:{Z:if(!(J<Z)){for(let Y=$+2;;){if(Z===void 0){if(J<W)break Z;return $=Q.length,this._cachedIndex=$,this.copySampleValue_($-1)}if($===Y)break;if(W=Z,Z=Q[++$],J<Z)break J}H=Q.length;break Q}if(!(J>=W)){let Y=Q[1];if(J<Y)$=2,W=Y;for(let X=$-2;;){if(W===void 0)return this._cachedIndex=0,this.copySampleValue_(0);if($===X)break;if(Z=W,W=Q[--$-1],J>=W)break J}H=$,$=0;break Q}break $}while($<H){let Y=$+H>>>1;if(J<Q[Y])H=Y;else $=Y+1}if(Z=Q[$],W=Q[$-1],W===void 0)return this._cachedIndex=0,this.copySampleValue_(0);if(Z===void 0)return $=Q.length,this._cachedIndex=$,this.copySampleValue_($-1)}this._cachedIndex=$,this.intervalChanged_($,W,Z)}return this.interpolate_($,W,J,Z)}getSettings_(){return this.settings||this.DefaultSettings_}copySampleValue_(J){let Q=this.resultBuffer,$=this.sampleValues,Z=this.valueSize,W=J*Z;for(let H=0;H!==Z;++H)Q[H]=$[W+H];return Q}interpolate_(){throw new Error("call to abstract method")}intervalChanged_(){}}class B$ extends u8{constructor(J,Q,$,Z){super(J,Q,$,Z);this._weightPrev=-0,this._offsetPrev=-0,this._weightNext=-0,this._offsetNext=-0,this.DefaultSettings_={endingStart:2400,endingEnd:2400}}intervalChanged_(J,Q,$){let Z=this.parameterPositions,W=J-2,H=J+1,Y=Z[W],X=Z[H];if(Y===void 0)switch(this.getSettings_().endingStart){case 2401:W=J,Y=2*Q-$;break;case 2402:W=Z.length-2,Y=Q+Z[W]-Z[W+1];break;default:W=J,Y=$}if(X===void 0)switch(this.getSettings_().endingEnd){case 2401:H=J,X=2*$-Q;break;case 2402:H=1,X=$+Z[1]-Z[0];break;default:H=J-1,X=Q}let K=($-Q)*0.5,U=this.valueSize;this._weightPrev=K/(Q-Y),this._weightNext=K/(X-$),this._offsetPrev=W*U,this._offsetNext=H*U}interpolate_(J,Q,$,Z){let W=this.resultBuffer,H=this.sampleValues,Y=this.valueSize,X=J*Y,K=X-Y,U=this._offsetPrev,G=this._offsetNext,q=this._weightPrev,E=this._weightNext,F=($-Q)/(Z-Q),k=F*F,M=k*F,N=-q*M+2*q*k-q*F,O=(1+q)*M+(-1.5-2*q)*k+(-0.5+q)*F+1,C=(-1-E)*M+(1.5+E)*k+0.5*F,L=E*M-E*k;for(let w=0;w!==Y;++w)W[w]=N*H[U+w]+O*H[K+w]+C*H[X+w]+L*H[G+w];return W}}class C$ extends u8{constructor(J,Q,$,Z){super(J,Q,$,Z)}interpolate_(J,Q,$,Z){let W=this.resultBuffer,H=this.sampleValues,Y=this.valueSize,X=J*Y,K=X-Y,U=($-Q)/(Z-Q),G=1-U;for(let q=0;q!==Y;++q)W[q]=H[K+q]*G+H[X+q]*U;return W}}class w$ extends u8{constructor(J,Q,$,Z){super(J,Q,$,Z)}interpolate_(J){return this.copySampleValue_(J-1)}}class d0{constructor(J,Q,$,Z){if(J===void 0)throw new Error("THREE.KeyframeTrack: track name is undefined");if(Q===void 0||Q.length===0)throw new Error("THREE.KeyframeTrack: no keyframes in track named "+J);this.name=J,this.times=t6(Q,this.TimeBufferType),this.values=t6($,this.ValueBufferType),this.setInterpolation(Z||this.DefaultInterpolation)}static toJSON(J){let Q=J.constructor,$;if(Q.toJSON!==this.toJSON)$=Q.toJSON(J);else{$={name:J.name,times:t6(J.times,Array),values:t6(J.values,Array)};let Z=J.getInterpolation();if(Z!==J.DefaultInterpolation)$.interpolation=Z}return $.type=J.ValueTypeName,$}InterpolantFactoryMethodDiscrete(J){return new w$(this.times,this.values,this.getValueSize(),J)}InterpolantFactoryMethodLinear(J){return new C$(this.times,this.values,this.getValueSize(),J)}InterpolantFactoryMethodSmooth(J){return new B$(this.times,this.values,this.getValueSize(),J)}setInterpolation(J){let Q;switch(J){case 2300:Q=this.InterpolantFactoryMethodDiscrete;break;case 2301:Q=this.InterpolantFactoryMethodLinear;break;case 2302:Q=this.InterpolantFactoryMethodSmooth;break}if(Q===void 0){let $="unsupported interpolation for "+this.ValueTypeName+" keyframe track named "+this.name;if(this.createInterpolant===void 0)if(J!==this.DefaultInterpolation)this.setInterpolation(this.DefaultInterpolation);else throw new Error($);return console.warn("THREE.KeyframeTrack:",$),this}return this.createInterpolant=Q,this}getInterpolation(){switch(this.createInterpolant){case this.InterpolantFactoryMethodDiscrete:return 2300;case this.InterpolantFactoryMethodLinear:return 2301;case this.InterpolantFactoryMethodSmooth:return 2302}}getValueSize(){return this.values.length/this.times.length}shift(J){if(J!==0){let Q=this.times;for(let $=0,Z=Q.length;$!==Z;++$)Q[$]+=J}return this}scale(J){if(J!==1){let Q=this.times;for(let $=0,Z=Q.length;$!==Z;++$)Q[$]*=J}return this}trim(J,Q){let $=this.times,Z=$.length,W=0,H=Z-1;while(W!==Z&&$[W]<J)++W;while(H!==-1&&$[H]>Q)--H;if(++H,W!==0||H!==Z){if(W>=H)H=Math.max(H,1),W=H-1;let Y=this.getValueSize();this.times=$.slice(W,H),this.values=this.values.slice(W*Y,H*Y)}return this}validate(){let J=!0,Q=this.getValueSize();if(Q-Math.floor(Q)!==0)console.error("THREE.KeyframeTrack: Invalid value size in track.",this),J=!1;let $=this.times,Z=this.values,W=$.length;if(W===0)console.error("THREE.KeyframeTrack: Track is empty.",this),J=!1;let H=null;for(let Y=0;Y!==W;Y++){let X=$[Y];if(typeof X==="number"&&isNaN(X)){console.error("THREE.KeyframeTrack: Time is not a valid number.",this,Y,X),J=!1;break}if(H!==null&&H>X){console.error("THREE.KeyframeTrack: Out of order keys.",this,Y,X,H),J=!1;break}H=X}if(Z!==void 0){if($X(Z))for(let Y=0,X=Z.length;Y!==X;++Y){let K=Z[Y];if(isNaN(K)){console.error("THREE.KeyframeTrack: Value is not a valid number.",this,Y,K),J=!1;break}}}return J}optimize(){let J=this.times.slice(),Q=this.values.slice(),$=this.getValueSize(),Z=this.getInterpolation()===2302,W=J.length-1,H=1;for(let Y=1;Y<W;++Y){let X=!1,K=J[Y],U=J[Y+1];if(K!==U&&(Y!==1||K!==J[0]))if(!Z){let G=Y*$,q=G-$,E=G+$;for(let F=0;F!==$;++F){let k=Q[G+F];if(k!==Q[q+F]||k!==Q[E+F]){X=!0;break}}}else X=!0;if(X){if(Y!==H){J[H]=J[Y];let G=Y*$,q=H*$;for(let E=0;E!==$;++E)Q[q+E]=Q[G+E]}++H}}if(W>0){J[H]=J[W];for(let Y=W*$,X=H*$,K=0;K!==$;++K)Q[X+K]=Q[Y+K];++H}if(H!==J.length)this.times=J.slice(0,H),this.values=Q.slice(0,H*$);else this.times=J,this.values=Q;return this}clone(){let J=this.times.slice(),Q=this.values.slice(),Z=new this.constructor(this.name,J,Q);return Z.createInterpolant=this.createInterpolant,Z}}d0.prototype.ValueTypeName="";d0.prototype.TimeBufferType=Float32Array;d0.prototype.ValueBufferType=Float32Array;d0.prototype.DefaultInterpolation=2301;class c8 extends d0{constructor(J,Q,$){super(J,Q,$)}}c8.prototype.ValueTypeName="bool";c8.prototype.ValueBufferType=Array;c8.prototype.DefaultInterpolation=2300;c8.prototype.InterpolantFactoryMethodLinear=void 0;c8.prototype.InterpolantFactoryMethodSmooth=void 0;class v7 extends d0{constructor(J,Q,$,Z){super(J,Q,$,Z)}}v7.prototype.ValueTypeName="color";class L8 extends d0{constructor(J,Q,$,Z){super(J,Q,$,Z)}}L8.prototype.ValueTypeName="number";class _$ extends u8{constructor(J,Q,$,Z){super(J,Q,$,Z)}interpolate_(J,Q,$,Z){let W=this.resultBuffer,H=this.sampleValues,Y=this.valueSize,X=($-Q)/(Z-Q),K=J*Y;for(let U=K+Y;K!==U;K+=4)A0.slerpFlat(W,0,H,K-Y,H,K,X);return W}}class I8 extends d0{constructor(J,Q,$,Z){super(J,Q,$,Z)}InterpolantFactoryMethodLinear(J){return new _$(this.times,this.values,this.getValueSize(),J)}}I8.prototype.ValueTypeName="quaternion";I8.prototype.InterpolantFactoryMethodSmooth=void 0;class n8 extends d0{constructor(J,Q,$){super(J,Q,$)}}n8.prototype.ValueTypeName="string";n8.prototype.ValueBufferType=Array;n8.prototype.DefaultInterpolation=2300;n8.prototype.InterpolantFactoryMethodLinear=void 0;n8.prototype.InterpolantFactoryMethodSmooth=void 0;class V8 extends d0{constructor(J,Q,$,Z){super(J,Q,$,Z)}}V8.prototype.ValueTypeName="vector";class f7{constructor(J="",Q=-1,$=[],Z=2500){if(this.name=J,this.tracks=$,this.duration=Q,this.blendMode=Z,this.uuid=Q8(),this.duration<0)this.resetDuration()}static parse(J){let Q=[],$=J.tracks,Z=1/(J.fps||1);for(let H=0,Y=$.length;H!==Y;++H)Q.push(HX($[H]).scale(Z));let W=new this(J.name,J.duration,Q,J.blendMode);return W.uuid=J.uuid,W}static toJSON(J){let Q=[],$=J.tracks,Z={name:J.name,duration:J.duration,tracks:Q,uuid:J.uuid,blendMode:J.blendMode};for(let W=0,H=$.length;W!==H;++W)Q.push(d0.toJSON($[W]));return Z}static CreateFromMorphTargetSequence(J,Q,$,Z){let W=Q.length,H=[];for(let Y=0;Y<W;Y++){let X=[],K=[];X.push((Y+W-1)%W,Y,(Y+1)%W),K.push(0,1,0);let U=ZX(X);if(X=xZ(X,1,U),K=xZ(K,1,U),!Z&&X[0]===0)X.push(W),K.push(K[0]);H.push(new L8(".morphTargetInfluences["+Q[Y].name+"]",X,K).scale(1/$))}return new this(J,-1,H)}static findByName(J,Q){let $=J;if(!Array.isArray(J)){let Z=J;$=Z.geometry&&Z.geometry.animations||Z.animations}for(let Z=0;Z<$.length;Z++)if($[Z].name===Q)return $[Z];return null}static CreateClipsFromMorphTargetSequences(J,Q,$){let Z={},W=/^([\w-]*?)([\d]+)$/;for(let Y=0,X=J.length;Y<X;Y++){let K=J[Y],U=K.name.match(W);if(U&&U.length>1){let G=U[1],q=Z[G];if(!q)Z[G]=q=[];q.push(K)}}let H=[];for(let Y in Z)H.push(this.CreateFromMorphTargetSequence(Y,Z[Y],Q,$));return H}static parseAnimation(J,Q){if(console.warn("THREE.AnimationClip: parseAnimation() is deprecated and will be removed with r185"),!J)return console.error("THREE.AnimationClip: No animation in JSONLoader data."),null;let $=function(G,q,E,F,k){if(E.length!==0){let M=[],N=[];if(uW(E,M,N,F),M.length!==0)k.push(new G(q,M,N))}},Z=[],W=J.name||"default",H=J.fps||30,Y=J.blendMode,X=J.length||-1,K=J.hierarchy||[];for(let G=0;G<K.length;G++){let q=K[G].keys;if(!q||q.length===0)continue;if(q[0].morphTargets){let E={},F;for(F=0;F<q.length;F++)if(q[F].morphTargets)for(let k=0;k<q[F].morphTargets.length;k++)E[q[F].morphTargets[k]]=-1;for(let k in E){let M=[],N=[];for(let O=0;O!==q[F].morphTargets.length;++O){let C=q[F];M.push(C.time),N.push(C.morphTarget===k?1:0)}Z.push(new L8(".morphTargetInfluence["+k+"]",M,N))}X=E.length*H}else{let E=".bones["+Q[G].name+"]";$(V8,E+".position",q,"pos",Z),$(I8,E+".quaternion",q,"rot",Z),$(V8,E+".scale",q,"scl",Z)}}if(Z.length===0)return null;return new this(W,X,Z,Y)}resetDuration(){let J=this.tracks,Q=0;for(let $=0,Z=J.length;$!==Z;++$){let W=this.tracks[$];Q=Math.max(Q,W.times[W.times.length-1])}return this.duration=Q,this}trim(){for(let J=0;J<this.tracks.length;J++)this.tracks[J].trim(0,this.duration);return this}validate(){let J=!0;for(let Q=0;Q<this.tracks.length;Q++)J=J&&this.tracks[Q].validate();return J}optimize(){for(let J=0;J<this.tracks.length;J++)this.tracks[J].optimize();return this}clone(){let J=[];for(let Q=0;Q<this.tracks.length;Q++)J.push(this.tracks[Q].clone());return new this.constructor(this.name,this.duration,J,this.blendMode)}toJSON(){return this.constructor.toJSON(this)}}function WX(J){switch(J.toLowerCase()){case"scalar":case"double":case"float":case"number":case"integer":return L8;case"vector":case"vector2":case"vector3":case"vector4":return V8;case"color":return v7;case"quaternion":return I8;case"bool":case"boolean":return c8;case"string":return n8}throw new Error("THREE.KeyframeTrack: Unsupported typeName: "+J)}function HX(J){if(J.type===void 0)throw new Error("THREE.KeyframeTrack: track type undefined, can not parse");let Q=WX(J.type);if(J.times===void 0){let $=[],Z=[];uW(J.keys,$,Z,"value"),J.times=$,J.values=Z}if(Q.parse!==void 0)return Q.parse(J);else return new Q(J.name,J.times,J.values,J.interpolation)}var X8={enabled:!1,files:{},add:function(J,Q){if(this.enabled===!1)return;this.files[J]=Q},get:function(J){if(this.enabled===!1)return;return this.files[J]},remove:function(J){delete this.files[J]},clear:function(){this.files={}}};class I${constructor(J,Q,$){let Z=this,W=!1,H=0,Y=0,X=void 0,K=[];this.onStart=void 0,this.onLoad=J,this.onProgress=Q,this.onError=$,this.abortController=new AbortController,this.itemStart=function(U){if(Y++,W===!1){if(Z.onStart!==void 0)Z.onStart(U,H,Y)}W=!0},this.itemEnd=function(U){if(H++,Z.onProgress!==void 0)Z.onProgress(U,H,Y);if(H===Y){if(W=!1,Z.onLoad!==void 0)Z.onLoad()}},this.itemError=function(U){if(Z.onError!==void 0)Z.onError(U)},this.resolveURL=function(U){if(X)return X(U);return U},this.setURLModifier=function(U){return X=U,this},this.addHandler=function(U,G){return K.push(U,G),this},this.removeHandler=function(U){let G=K.indexOf(U);if(G!==-1)K.splice(G,2);return this},this.getHandler=function(U){for(let G=0,q=K.length;G<q;G+=2){let E=K[G],F=K[G+1];if(E.global)E.lastIndex=0;if(E.test(U))return F}return null},this.abort=function(){return this.abortController.abort(),this.abortController=new AbortController,this}}}var cW=new I$;class P8{constructor(J){this.manager=J!==void 0?J:cW,this.crossOrigin="anonymous",this.withCredentials=!1,this.path="",this.resourcePath="",this.requestHeader={}}load(){}loadAsync(J,Q){let $=this;return new Promise(function(Z,W){$.load(J,Z,Q,W)})}parse(){}setCrossOrigin(J){return this.crossOrigin=J,this}setWithCredentials(J){return this.withCredentials=J,this}setPath(J){return this.path=J,this}setResourcePath(J){return this.resourcePath=J,this}setRequestHeader(J){return this.requestHeader=J,this}abort(){return this}}P8.DEFAULT_MATERIAL_NAME="__DEFAULT";var M8={};class nW extends Error{constructor(J,Q){super(J);this.response=Q}}class z6 extends P8{constructor(J){super(J);this.mimeType="",this.responseType="",this._abortController=new AbortController}load(J,Q,$,Z){if(J===void 0)J="";if(this.path!==void 0)J=this.path+J;J=this.manager.resolveURL(J);let W=X8.get(`file:${J}`);if(W!==void 0)return this.manager.itemStart(J),setTimeout(()=>{if(Q)Q(W);this.manager.itemEnd(J)},0),W;if(M8[J]!==void 0){M8[J].push({onLoad:Q,onProgress:$,onError:Z});return}M8[J]=[],M8[J].push({onLoad:Q,onProgress:$,onError:Z});let H=new Request(J,{headers:new Headers(this.requestHeader),credentials:this.withCredentials?"include":"same-origin",signal:typeof AbortSignal.any==="function"?AbortSignal.any([this._abortController.signal,this.manager.abortController.signal]):this._abortController.signal}),Y=this.mimeType,X=this.responseType;fetch(H).then((K)=>{if(K.status===200||K.status===0){if(K.status===0)console.warn("THREE.FileLoader: HTTP Status 0 received.");if(typeof ReadableStream==="undefined"||K.body===void 0||K.body.getReader===void 0)return K;let U=M8[J],G=K.body.getReader(),q=K.headers.get("X-File-Size")||K.headers.get("Content-Length"),E=q?parseInt(q):0,F=E!==0,k=0,M=new ReadableStream({start(N){O();function O(){G.read().then(({done:C,value:L})=>{if(C)N.close();else{k+=L.byteLength;let w=new ProgressEvent("progress",{lengthComputable:F,loaded:k,total:E});for(let v=0,_=U.length;v<_;v++){let T=U[v];if(T.onProgress)T.onProgress(w)}N.enqueue(L),O()}},(C)=>{N.error(C)})}}});return new Response(M)}else throw new nW(`fetch for "${K.url}" responded with ${K.status}: ${K.statusText}`,K)}).then((K)=>{switch(X){case"arraybuffer":return K.arrayBuffer();case"blob":return K.blob();case"document":return K.text().then((U)=>{return new DOMParser().parseFromString(U,Y)});case"json":return K.json();default:if(Y==="")return K.text();else{let G=/charset="?([^;"\s]*)"?/i.exec(Y),q=G&&G[1]?G[1].toLowerCase():void 0,E=new TextDecoder(q);return K.arrayBuffer().then((F)=>E.decode(F))}}}).then((K)=>{X8.add(`file:${J}`,K);let U=M8[J];delete M8[J];for(let G=0,q=U.length;G<q;G++){let E=U[G];if(E.onLoad)E.onLoad(K)}}).catch((K)=>{let U=M8[J];if(U===void 0)throw this.manager.itemError(J),K;delete M8[J];for(let G=0,q=U.length;G<q;G++){let E=U[G];if(E.onError)E.onError(K)}this.manager.itemError(J)}).finally(()=>{this.manager.itemEnd(J)}),this.manager.itemStart(J)}setResponseType(J){return this.responseType=J,this}setMimeType(J){return this.mimeType=J,this}abort(){return this._abortController.abort(),this._abortController=new AbortController,this}}var P9=new WeakMap;class P$ extends P8{constructor(J){super(J)}load(J,Q,$,Z){if(this.path!==void 0)J=this.path+J;J=this.manager.resolveURL(J);let W=this,H=X8.get(`image:${J}`);if(H!==void 0){if(H.complete===!0)W.manager.itemStart(J),setTimeout(function(){if(Q)Q(H);W.manager.itemEnd(J)},0);else{let G=P9.get(H);if(G===void 0)G=[],P9.set(H,G);G.push({onLoad:Q,onError:Z})}return H}let Y=A9("img");function X(){if(U(),Q)Q(this);let G=P9.get(this)||[];for(let q=0;q<G.length;q++){let E=G[q];if(E.onLoad)E.onLoad(this)}P9.delete(this),W.manager.itemEnd(J)}function K(G){if(U(),Z)Z(G);X8.remove(`image:${J}`);let q=P9.get(this)||[];for(let E=0;E<q.length;E++){let F=q[E];if(F.onError)F.onError(G)}P9.delete(this),W.manager.itemError(J),W.manager.itemEnd(J)}function U(){Y.removeEventListener("load",X,!1),Y.removeEventListener("error",K,!1)}if(Y.addEventListener("load",X,!1),Y.addEventListener("error",K,!1),J.slice(0,5)!=="data:"){if(this.crossOrigin!==void 0)Y.crossOrigin=this.crossOrigin}return X8.add(`image:${J}`,Y),W.manager.itemStart(J),Y.src=J,Y}}class h7 extends P8{constructor(J){super(J)}load(J,Q,$,Z){let W=new E0,H=new P$(this.manager);return H.setCrossOrigin(this.crossOrigin),H.setPath(this.path),H.load(J,function(Y){if(W.image=Y,W.needsUpdate=!0,Q!==void 0)Q(W)},$,Z),W}}class d9 extends Z0{constructor(J,Q=1){super();this.isLight=!0,this.type="Light",this.color=new jJ(J),this.intensity=Q}dispose(){}copy(J,Q){return super.copy(J,Q),this.color.copy(J.color),this.intensity=J.intensity,this}toJSON(J){let Q=super.toJSON(J);if(Q.object.color=this.color.getHex(),Q.object.intensity=this.intensity,this.groundColor!==void 0)Q.object.groundColor=this.groundColor.getHex();if(this.distance!==void 0)Q.object.distance=this.distance;if(this.angle!==void 0)Q.object.angle=this.angle;if(this.decay!==void 0)Q.object.decay=this.decay;if(this.penumbra!==void 0)Q.object.penumbra=this.penumbra;if(this.shadow!==void 0)Q.object.shadow=this.shadow.toJSON();if(this.target!==void 0)Q.object.target=this.target.uuid;return Q}}class b7 extends d9{constructor(J,Q,$){super(J,$);this.isHemisphereLight=!0,this.type="HemisphereLight",this.position.copy(Z0.DEFAULT_UP),this.updateMatrix(),this.groundColor=new jJ(Q)}copy(J,Q){return super.copy(J,Q),this.groundColor.copy(J.groundColor),this}}var LQ=new vJ,gZ=new A,pZ=new A;class x7{constructor(J){this.camera=J,this.intensity=1,this.bias=0,this.normalBias=0,this.radius=1,this.blurSamples=8,this.mapSize=new PJ(512,512),this.mapType=1009,this.map=null,this.mapPass=null,this.matrix=new vJ,this.autoUpdate=!0,this.needsUpdate=!1,this._frustum=new M6,this._frameExtents=new PJ(1,1),this._viewportCount=1,this._viewports=[new sJ(0,0,1,1)]}getViewportCount(){return this._viewportCount}getFrustum(){return this._frustum}updateMatrices(J){let Q=this.camera,$=this.matrix;if(gZ.setFromMatrixPosition(J.matrixWorld),Q.position.copy(gZ),pZ.setFromMatrixPosition(J.target.matrixWorld),Q.lookAt(pZ),Q.updateMatrixWorld(),LQ.multiplyMatrices(Q.projectionMatrix,Q.matrixWorldInverse),this._frustum.setFromProjectionMatrix(LQ,Q.coordinateSystem,Q.reversedDepth),Q.reversedDepth)$.set(0.5,0,0,0.5,0,0.5,0,0.5,0,0,1,0,0,0,0,1);else $.set(0.5,0,0,0.5,0,0.5,0,0.5,0,0,0.5,0.5,0,0,0,1);$.multiply(LQ)}getViewport(J){return this._viewports[J]}getFrameExtents(){return this._frameExtents}dispose(){if(this.map)this.map.dispose();if(this.mapPass)this.mapPass.dispose()}copy(J){return this.camera=J.camera.clone(),this.intensity=J.intensity,this.bias=J.bias,this.radius=J.radius,this.autoUpdate=J.autoUpdate,this.needsUpdate=J.needsUpdate,this.normalBias=J.normalBias,this.blurSamples=J.blurSamples,this.mapSize.copy(J.mapSize),this}clone(){return new this.constructor().copy(this)}toJSON(){let J={};if(this.intensity!==1)J.intensity=this.intensity;if(this.bias!==0)J.bias=this.bias;if(this.normalBias!==0)J.normalBias=this.normalBias;if(this.radius!==1)J.radius=this.radius;if(this.mapSize.x!==512||this.mapSize.y!==512)J.mapSize=this.mapSize.toArray();return J.camera=this.camera.toJSON(!1).object,delete J.camera.matrix,J}}class sW extends x7{constructor(){super(new O0(50,1,0.5,500));this.isSpotLightShadow=!0,this.focus=1,this.aspect=1}updateMatrices(J){let Q=this.camera,$=Q9*2*J.angle*this.focus,Z=this.mapSize.width/this.mapSize.height*this.aspect,W=J.distance||Q.far;if($!==Q.fov||Z!==Q.aspect||W!==Q.far)Q.fov=$,Q.aspect=Z,Q.far=W,Q.updateProjectionMatrix();super.updateMatrices(J)}copy(J){return super.copy(J),this.focus=J.focus,this}}class g7 extends d9{constructor(J,Q,$=0,Z=Math.PI/3,W=0,H=2){super(J,Q);this.isSpotLight=!0,this.type="SpotLight",this.position.copy(Z0.DEFAULT_UP),this.updateMatrix(),this.target=new Z0,this.distance=$,this.angle=Z,this.penumbra=W,this.decay=H,this.map=null,this.shadow=new sW}get power(){return this.intensity*Math.PI}set power(J){this.intensity=J/Math.PI}dispose(){this.shadow.dispose()}copy(J,Q){return super.copy(J,Q),this.distance=J.distance,this.angle=J.angle,this.penumbra=J.penumbra,this.decay=J.decay,this.target=J.target.clone(),this.shadow=J.shadow.clone(),this}}var lZ=new vJ,Z6=new A,VQ=new A;class oW extends x7{constructor(){super(new O0(90,1,0.5,500));this.isPointLightShadow=!0,this._frameExtents=new PJ(4,2),this._viewportCount=6,this._viewports=[new sJ(2,1,1,1),new sJ(0,1,1,1),new sJ(3,1,1,1),new sJ(1,1,1,1),new sJ(3,0,1,1),new sJ(1,0,1,1)],this._cubeDirections=[new A(1,0,0),new A(-1,0,0),new A(0,0,1),new A(0,0,-1),new A(0,1,0),new A(0,-1,0)],this._cubeUps=[new A(0,1,0),new A(0,1,0),new A(0,1,0),new A(0,1,0),new A(0,0,1),new A(0,0,-1)]}updateMatrices(J,Q=0){let $=this.camera,Z=this.matrix,W=J.distance||$.far;if(W!==$.far)$.far=W,$.updateProjectionMatrix();Z6.setFromMatrixPosition(J.matrixWorld),$.position.copy(Z6),VQ.copy($.position),VQ.add(this._cubeDirections[Q]),$.up.copy(this._cubeUps[Q]),$.lookAt(VQ),$.updateMatrixWorld(),Z.makeTranslation(-Z6.x,-Z6.y,-Z6.z),lZ.multiplyMatrices($.projectionMatrix,$.matrixWorldInverse),this._frustum.setFromProjectionMatrix(lZ,$.coordinateSystem,$.reversedDepth)}}class p7 extends d9{constructor(J,Q,$=0,Z=2){super(J,Q);this.isPointLight=!0,this.type="PointLight",this.distance=$,this.decay=Z,this.shadow=new oW}get power(){return this.intensity*4*Math.PI}set power(J){this.intensity=J/(4*Math.PI)}dispose(){this.shadow.dispose()}copy(J,Q){return super.copy(J,Q),this.distance=J.distance,this.decay=J.decay,this.shadow=J.shadow.clone(),this}}class m9 extends C7{constructor(J=-1,Q=1,$=1,Z=-1,W=0.1,H=2000){super();this.isOrthographicCamera=!0,this.type="OrthographicCamera",this.zoom=1,this.view=null,this.left=J,this.right=Q,this.top=$,this.bottom=Z,this.near=W,this.far=H,this.updateProjectionMatrix()}copy(J,Q){return super.copy(J,Q),this.left=J.left,this.right=J.right,this.top=J.top,this.bottom=J.bottom,this.near=J.near,this.far=J.far,this.zoom=J.zoom,this.view=J.view===null?null:Object.assign({},J.view),this}setViewOffset(J,Q,$,Z,W,H){if(this.view===null)this.view={enabled:!0,fullWidth:1,fullHeight:1,offsetX:0,offsetY:0,width:1,height:1};this.view.enabled=!0,this.view.fullWidth=J,this.view.fullHeight=Q,this.view.offsetX=$,this.view.offsetY=Z,this.view.width=W,this.view.height=H,this.updateProjectionMatrix()}clearViewOffset(){if(this.view!==null)this.view.enabled=!1;this.updateProjectionMatrix()}updateProjectionMatrix(){let J=(this.right-this.left)/(2*this.zoom),Q=(this.top-this.bottom)/(2*this.zoom),$=(this.right+this.left)/2,Z=(this.top+this.bottom)/2,W=$-J,H=$+J,Y=Z+Q,X=Z-Q;if(this.view!==null&&this.view.enabled){let K=(this.right-this.left)/this.view.fullWidth/this.zoom,U=(this.top-this.bottom)/this.view.fullHeight/this.zoom;W+=K*this.view.offsetX,H=W+K*this.view.width,Y-=U*this.view.offsetY,X=Y-U*this.view.height}this.projectionMatrix.makeOrthographic(W,H,Y,X,this.near,this.far,this.coordinateSystem,this.reversedDepth),this.projectionMatrixInverse.copy(this.projectionMatrix).invert()}toJSON(J){let Q=super.toJSON(J);if(Q.object.zoom=this.zoom,Q.object.left=this.left,Q.object.right=this.right,Q.object.top=this.top,Q.object.bottom=this.bottom,Q.object.near=this.near,Q.object.far=this.far,this.view!==null)Q.object.view=Object.assign({},this.view);return Q}}class iW extends x7{constructor(){super(new m9(-5,5,5,-5,0.5,500));this.isDirectionalLightShadow=!0}}class u9 extends d9{constructor(J,Q){super(J,Q);this.isDirectionalLight=!0,this.type="DirectionalLight",this.position.copy(Z0.DEFAULT_UP),this.updateMatrix(),this.target=new Z0,this.shadow=new iW}dispose(){this.shadow.dispose()}copy(J){return super.copy(J),this.target=J.target.clone(),this.shadow=J.shadow.clone(),this}}class s8{static extractUrlBase(J){let Q=J.lastIndexOf("/");if(Q===-1)return"./";return J.slice(0,Q+1)}static resolveURL(J,Q){if(typeof J!=="string"||J==="")return"";if(/^https?:\/\//i.test(Q)&&/^\//.test(J))Q=Q.replace(/(^https?:\/\/[^\/]+).*/i,"$1");if(/^(https?:)?\/\//i.test(J))return J;if(/^data:.*,.*$/i.test(J))return J;if(/^blob:.*$/i.test(J))return J;return Q+J}}var zQ=new WeakMap;class l7 extends P8{constructor(J){super(J);if(this.isImageBitmapLoader=!0,typeof createImageBitmap==="undefined")console.warn("THREE.ImageBitmapLoader: createImageBitmap() not supported.");if(typeof fetch==="undefined")console.warn("THREE.ImageBitmapLoader: fetch() not supported.");this.options={premultiplyAlpha:"none"},this._abortController=new AbortController}setOptions(J){return this.options=J,this}load(J,Q,$,Z){if(J===void 0)J="";if(this.path!==void 0)J=this.path+J;J=this.manager.resolveURL(J);let W=this,H=X8.get(`image-bitmap:${J}`);if(H!==void 0){if(W.manager.itemStart(J),H.then){H.then((K)=>{if(zQ.has(H)===!0){if(Z)Z(zQ.get(H));W.manager.itemError(J),W.manager.itemEnd(J)}else{if(Q)Q(K);return W.manager.itemEnd(J),K}});return}return setTimeout(function(){if(Q)Q(H);W.manager.itemEnd(J)},0),H}let Y={};Y.credentials=this.crossOrigin==="anonymous"?"same-origin":"include",Y.headers=this.requestHeader,Y.signal=typeof AbortSignal.any==="function"?AbortSignal.any([this._abortController.signal,this.manager.abortController.signal]):this._abortController.signal;let X=fetch(J,Y).then(function(K){return K.blob()}).then(function(K){return createImageBitmap(K,Object.assign(W.options,{colorSpaceConversion:"none"}))}).then(function(K){if(X8.add(`image-bitmap:${J}`,K),Q)Q(K);return W.manager.itemEnd(J),K}).catch(function(K){if(Z)Z(K);zQ.set(X,K),X8.remove(`image-bitmap:${J}`),W.manager.itemError(J),W.manager.itemEnd(J)});X8.add(`image-bitmap:${J}`,X),W.manager.itemStart(J)}abort(){return this._abortController.abort(),this._abortController=new AbortController,this}}class T$ extends O0{constructor(J=[]){super();this.isArrayCamera=!0,this.isMultiViewCamera=!1,this.cameras=J}}var A$="\\[\\]\\.:\\/",YX=new RegExp("["+A$+"]","g"),S$="[^"+A$+"]",XX="[^"+A$.replace("\\.","")+"]",KX=/((?:WC+[\/:])*)/.source.replace("WC",S$),UX=/(WCOD+)?/.source.replace("WCOD",XX),GX=/(?:\.(WC+)(?:\[(.+)\])?)?/.source.replace("WC",S$),qX=/\.(WC+)(?:\[(.+)\])?/.source.replace("WC",S$),EX=new RegExp("^"+KX+UX+GX+qX+"$"),NX=["material","materials","bones","map"];class aW{constructor(J,Q,$){let Z=$||oJ.parseTrackName(Q);this._targetGroup=J,this._bindings=J.subscribe_(Q,Z)}getValue(J,Q){this.bind();let $=this._targetGroup.nCachedObjects_,Z=this._bindings[$];if(Z!==void 0)Z.getValue(J,Q)}setValue(J,Q){let $=this._bindings;for(let Z=this._targetGroup.nCachedObjects_,W=$.length;Z!==W;++Z)$[Z].setValue(J,Q)}bind(){let J=this._bindings;for(let Q=this._targetGroup.nCachedObjects_,$=J.length;Q!==$;++Q)J[Q].bind()}unbind(){let J=this._bindings;for(let Q=this._targetGroup.nCachedObjects_,$=J.length;Q!==$;++Q)J[Q].unbind()}}class oJ{constructor(J,Q,$){this.path=Q,this.parsedPath=$||oJ.parseTrackName(Q),this.node=oJ.findNode(J,this.parsedPath.nodeName),this.rootNode=J,this.getValue=this._getValue_unbound,this.setValue=this._setValue_unbound}static create(J,Q,$){if(!(J&&J.isAnimationObjectGroup))return new oJ(J,Q,$);else return new oJ.Composite(J,Q,$)}static sanitizeNodeName(J){return J.replace(/\s/g,"_").replace(YX,"")}static parseTrackName(J){let Q=EX.exec(J);if(Q===null)throw new Error("PropertyBinding: Cannot parse trackName: "+J);let $={nodeName:Q[2],objectName:Q[3],objectIndex:Q[4],propertyName:Q[5],propertyIndex:Q[6]},Z=$.nodeName&&$.nodeName.lastIndexOf(".");if(Z!==void 0&&Z!==-1){let W=$.nodeName.substring(Z+1);if(NX.indexOf(W)!==-1)$.nodeName=$.nodeName.substring(0,Z),$.objectName=W}if($.propertyName===null||$.propertyName.length===0)throw new Error("PropertyBinding: can not parse propertyName from trackName: "+J);return $}static findNode(J,Q){if(Q===void 0||Q===""||Q==="."||Q===-1||Q===J.name||Q===J.uuid)return J;if(J.skeleton){let $=J.skeleton.getBoneByName(Q);if($!==void 0)return $}if(J.children){let $=function(W){for(let H=0;H<W.length;H++){let Y=W[H];if(Y.name===Q||Y.uuid===Q)return Y;let X=$(Y.children);if(X)return X}return null},Z=$(J.children);if(Z)return Z}return null}_getValue_unavailable(){}_setValue_unavailable(){}_getValue_direct(J,Q){J[Q]=this.targetObject[this.propertyName]}_getValue_array(J,Q){let $=this.resolvedProperty;for(let Z=0,W=$.length;Z!==W;++Z)J[Q++]=$[Z]}_getValue_arrayElement(J,Q){J[Q]=this.resolvedProperty[this.propertyIndex]}_getValue_toArray(J,Q){this.resolvedProperty.toArray(J,Q)}_setValue_direct(J,Q){this.targetObject[this.propertyName]=J[Q]}_setValue_direct_setNeedsUpdate(J,Q){this.targetObject[this.propertyName]=J[Q],this.targetObject.needsUpdate=!0}_setValue_direct_setMatrixWorldNeedsUpdate(J,Q){this.targetObject[this.propertyName]=J[Q],this.targetObject.matrixWorldNeedsUpdate=!0}_setValue_array(J,Q){let $=this.resolvedProperty;for(let Z=0,W=$.length;Z!==W;++Z)$[Z]=J[Q++]}_setValue_array_setNeedsUpdate(J,Q){let $=this.resolvedProperty;for(let Z=0,W=$.length;Z!==W;++Z)$[Z]=J[Q++];this.targetObject.needsUpdate=!0}_setValue_array_setMatrixWorldNeedsUpdate(J,Q){let $=this.resolvedProperty;for(let Z=0,W=$.length;Z!==W;++Z)$[Z]=J[Q++];this.targetObject.matrixWorldNeedsUpdate=!0}_setValue_arrayElement(J,Q){this.resolvedProperty[this.propertyIndex]=J[Q]}_setValue_arrayElement_setNeedsUpdate(J,Q){this.resolvedProperty[this.propertyIndex]=J[Q],this.targetObject.needsUpdate=!0}_setValue_arrayElement_setMatrixWorldNeedsUpdate(J,Q){this.resolvedProperty[this.propertyIndex]=J[Q],this.targetObject.matrixWorldNeedsUpdate=!0}_setValue_fromArray(J,Q){this.resolvedProperty.fromArray(J,Q)}_setValue_fromArray_setNeedsUpdate(J,Q){this.resolvedProperty.fromArray(J,Q),this.targetObject.needsUpdate=!0}_setValue_fromArray_setMatrixWorldNeedsUpdate(J,Q){this.resolvedProperty.fromArray(J,Q),this.targetObject.matrixWorldNeedsUpdate=!0}_getValue_unbound(J,Q){this.bind(),this.getValue(J,Q)}_setValue_unbound(J,Q){this.bind(),this.setValue(J,Q)}bind(){let J=this.node,Q=this.parsedPath,$=Q.objectName,Z=Q.propertyName,W=Q.propertyIndex;if(!J)J=oJ.findNode(this.rootNode,Q.nodeName),this.node=J;if(this.getValue=this._getValue_unavailable,this.setValue=this._setValue_unavailable,!J){console.warn("THREE.PropertyBinding: No target node found for track: "+this.path+".");return}if($){let K=Q.objectIndex;switch($){case"materials":if(!J.material){console.error("THREE.PropertyBinding: Can not bind to material as node does not have a material.",this);return}if(!J.material.materials){console.error("THREE.PropertyBinding: Can not bind to material.materials as node.material does not have a materials array.",this);return}J=J.material.materials;break;case"bones":if(!J.skeleton){console.error("THREE.PropertyBinding: Can not bind to bones as node does not have a skeleton.",this);return}J=J.skeleton.bones;for(let U=0;U<J.length;U++)if(J[U].name===K){K=U;break}break;case"map":if("map"in J){J=J.map;break}if(!J.material){console.error("THREE.PropertyBinding: Can not bind to material as node does not have a material.",this);return}if(!J.material.map){console.error("THREE.PropertyBinding: Can not bind to material.map as node.material does not have a map.",this);return}J=J.material.map;break;default:if(J[$]===void 0){console.error("THREE.PropertyBinding: Can not bind to objectName of node undefined.",this);return}J=J[$]}if(K!==void 0){if(J[K]===void 0){console.error("THREE.PropertyBinding: Trying to bind to objectIndex of objectName, but is undefined.",this,J);return}J=J[K]}}let H=J[Z];if(H===void 0){let K=Q.nodeName;console.error("THREE.PropertyBinding: Trying to update property for track: "+K+"."+Z+" but it wasn't found.",J);return}let Y=this.Versioning.None;if(this.targetObject=J,J.isMaterial===!0)Y=this.Versioning.NeedsUpdate;else if(J.isObject3D===!0)Y=this.Versioning.MatrixWorldNeedsUpdate;let X=this.BindingType.Direct;if(W!==void 0){if(Z==="morphTargetInfluences"){if(!J.geometry){console.error("THREE.PropertyBinding: Can not bind to morphTargetInfluences because node does not have a geometry.",this);return}if(!J.geometry.morphAttributes){console.error("THREE.PropertyBinding: Can not bind to morphTargetInfluences because node does not have a geometry.morphAttributes.",this);return}if(J.morphTargetDictionary[W]!==void 0)W=J.morphTargetDictionary[W]}X=this.BindingType.ArrayElement,this.resolvedProperty=H,this.propertyIndex=W}else if(H.fromArray!==void 0&&H.toArray!==void 0)X=this.BindingType.HasFromToArray,this.resolvedProperty=H;else if(Array.isArray(H))X=this.BindingType.EntireArray,this.resolvedProperty=H;else this.propertyName=Z;this.getValue=this.GetterByBindingType[X],this.setValue=this.SetterByBindingTypeAndVersioning[X][Y]}unbind(){this.node=null,this.getValue=this._getValue_unbound,this.setValue=this._setValue_unbound}}oJ.Composite=aW;oJ.prototype.BindingType={Direct:0,EntireArray:1,ArrayElement:2,HasFromToArray:3};oJ.prototype.Versioning={None:0,NeedsUpdate:1,MatrixWorldNeedsUpdate:2};oJ.prototype.GetterByBindingType=[oJ.prototype._getValue_direct,oJ.prototype._getValue_array,oJ.prototype._getValue_arrayElement,oJ.prototype._getValue_toArray];oJ.prototype.SetterByBindingTypeAndVersioning=[[oJ.prototype._setValue_direct,oJ.prototype._setValue_direct_setNeedsUpdate,oJ.prototype._setValue_direct_setMatrixWorldNeedsUpdate],[oJ.prototype._setValue_array,oJ.prototype._setValue_array_setNeedsUpdate,oJ.prototype._setValue_array_setMatrixWorldNeedsUpdate],[oJ.prototype._setValue_arrayElement,oJ.prototype._setValue_arrayElement_setNeedsUpdate,oJ.prototype._setValue_arrayElement_setMatrixWorldNeedsUpdate],[oJ.prototype._setValue_fromArray,oJ.prototype._setValue_fromArray_setNeedsUpdate,oJ.prototype._setValue_fromArray_setMatrixWorldNeedsUpdate]];var Fq=new Float32Array(1);class B6{constructor(J=1,Q=0,$=0){this.radius=J,this.phi=Q,this.theta=$}set(J,Q,$){return this.radius=J,this.phi=Q,this.theta=$,this}copy(J){return this.radius=J.radius,this.phi=J.phi,this.theta=J.theta,this}makeSafe(){return this.phi=xJ(this.phi,0.000001,Math.PI-0.000001),this}setFromVector3(J){return this.setFromCartesianCoords(J.x,J.y,J.z)}setFromCartesianCoords(J,Q,$){if(this.radius=Math.sqrt(J*J+Q*Q+$*$),this.radius===0)this.theta=0,this.phi=0;else this.theta=Math.atan2(J,$),this.phi=Math.acos(xJ(Q/this.radius,-1,1));return this}clone(){return new this.constructor().copy(this)}}class d7 extends w8{constructor(J,Q=null){super();this.object=J,this.domElement=Q,this.enabled=!0,this.state=-1,this.keys={},this.mouseButtons={LEFT:null,MIDDLE:null,RIGHT:null},this.touches={ONE:null,TWO:null}}connect(J){if(J===void 0){console.warn("THREE.Controls: connect() now requires an element.");return}if(this.domElement!==null)this.disconnect();this.domElement=J}disconnect(){}dispose(){}update(){}}function j$(J,Q,$,Z){let W=OX(Z);switch($){case 1021:return J*Q;case 1028:return J*Q/W.components*W.byteLength;case 1029:return J*Q/W.components*W.byteLength;case 1030:return J*Q*2/W.components*W.byteLength;case 1031:return J*Q*2/W.components*W.byteLength;case 1022:return J*Q*3/W.components*W.byteLength;case 1023:return J*Q*4/W.components*W.byteLength;case 1033:return J*Q*4/W.components*W.byteLength;case 33776:case 33777:return Math.floor((J+3)/4)*Math.floor((Q+3)/4)*8;case 33778:case 33779:return Math.floor((J+3)/4)*Math.floor((Q+3)/4)*16;case 35841:case 35843:return Math.max(J,16)*Math.max(Q,8)/4;case 35840:case 35842:return Math.max(J,8)*Math.max(Q,8)/2;case 36196:case 37492:return Math.floor((J+3)/4)*Math.floor((Q+3)/4)*8;case 37496:return Math.floor((J+3)/4)*Math.floor((Q+3)/4)*16;case 37808:return Math.floor((J+3)/4)*Math.floor((Q+3)/4)*16;case 37809:return Math.floor((J+4)/5)*Math.floor((Q+3)/4)*16;case 37810:return Math.floor((J+4)/5)*Math.floor((Q+4)/5)*16;case 37811:return Math.floor((J+5)/6)*Math.floor((Q+4)/5)*16;case 37812:return Math.floor((J+5)/6)*Math.floor((Q+5)/6)*16;case 37813:return Math.floor((J+7)/8)*Math.floor((Q+4)/5)*16;case 37814:return Math.floor((J+7)/8)*Math.floor((Q+5)/6)*16;case 37815:return Math.floor((J+7)/8)*Math.floor((Q+7)/8)*16;case 37816:return Math.floor((J+9)/10)*Math.floor((Q+4)/5)*16;case 37817:return Math.floor((J+9)/10)*Math.floor((Q+5)/6)*16;case 37818:return Math.floor((J+9)/10)*Math.floor((Q+7)/8)*16;case 37819:return Math.floor((J+9)/10)*Math.floor((Q+9)/10)*16;case 37820:return Math.floor((J+11)/12)*Math.floor((Q+9)/10)*16;case 37821:return Math.floor((J+11)/12)*Math.floor((Q+11)/12)*16;case 36492:case 36494:case 36495:return Math.ceil(J/4)*Math.ceil(Q/4)*16;case 36283:case 36284:return Math.ceil(J/4)*Math.ceil(Q/4)*8;case 36285:case 36286:return Math.ceil(J/4)*Math.ceil(Q/4)*16}throw new Error(`Unable to determine texture byte length for ${$} format.`)}function OX(J){switch(J){case 1009:case 1010:return{byteLength:1,components:1};case 1012:case 1011:case 1016:return{byteLength:2,components:1};case 1017:case 1018:return{byteLength:2,components:4};case 1014:case 1013:case 1015:return{byteLength:4,components:1};case 35902:return{byteLength:4,components:3}}throw new Error(`Unknown texture type ${J}.`)}if(typeof __THREE_DEVTOOLS__!=="undefined")__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("register",{detail:{revision:"179"}}));if(typeof window!=="undefined")if(window.__THREE__)console.warn("WARNING: Multiple instances of Three.js being imported.");else window.__THREE__="179";function LH(){let J=null,Q=!1,$=null,Z=null;function W(H,Y){$(H,Y),Z=J.requestAnimationFrame(W)}return{start:function(){if(Q===!0)return;if($===null)return;Z=J.requestAnimationFrame(W),Q=!0},stop:function(){J.cancelAnimationFrame(Z),Q=!1},setAnimationLoop:function(H){$=H},setContext:function(H){J=H}}}function FX(J){let Q=new WeakMap;function $(X,K){let{array:U,usage:G}=X,q=U.byteLength,E=J.createBuffer();J.bindBuffer(K,E),J.bufferData(K,U,G),X.onUploadCallback();let F;if(U instanceof Float32Array)F=J.FLOAT;else if(typeof Float16Array!=="undefined"&&U instanceof Float16Array)F=J.HALF_FLOAT;else if(U instanceof Uint16Array)if(X.isFloat16BufferAttribute)F=J.HALF_FLOAT;else F=J.UNSIGNED_SHORT;else if(U instanceof Int16Array)F=J.SHORT;else if(U instanceof Uint32Array)F=J.UNSIGNED_INT;else if(U instanceof Int32Array)F=J.INT;else if(U instanceof Int8Array)F=J.BYTE;else if(U instanceof Uint8Array)F=J.UNSIGNED_BYTE;else if(U instanceof Uint8ClampedArray)F=J.UNSIGNED_BYTE;else throw new Error("THREE.WebGLAttributes: Unsupported buffer data format: "+U);return{buffer:E,type:F,bytesPerElement:U.BYTES_PER_ELEMENT,version:X.version,size:q}}function Z(X,K,U){let{array:G,updateRanges:q}=K;if(J.bindBuffer(U,X),q.length===0)J.bufferSubData(U,0,G);else{q.sort((F,k)=>F.start-k.start);let E=0;for(let F=1;F<q.length;F++){let k=q[E],M=q[F];if(M.start<=k.start+k.count+1)k.count=Math.max(k.count,M.start+M.count-k.start);else++E,q[E]=M}q.length=E+1;for(let F=0,k=q.length;F<k;F++){let M=q[F];J.bufferSubData(U,M.start*G.BYTES_PER_ELEMENT,G,M.start,M.count)}K.clearUpdateRanges()}K.onUploadCallback()}function W(X){if(X.isInterleavedBufferAttribute)X=X.data;return Q.get(X)}function H(X){if(X.isInterleavedBufferAttribute)X=X.data;let K=Q.get(X);if(K)J.deleteBuffer(K.buffer),Q.delete(X)}function Y(X,K){if(X.isInterleavedBufferAttribute)X=X.data;if(X.isGLBufferAttribute){let G=Q.get(X);if(!G||G.version<X.version)Q.set(X,{buffer:X.buffer,type:X.type,bytesPerElement:X.elementSize,version:X.version});return}let U=Q.get(X);if(U===void 0)Q.set(X,$(X,K));else if(U.version<X.version){if(U.size!==X.array.byteLength)throw new Error("THREE.WebGLAttributes: The size of the buffer attribute's array buffer does not match the original size. Resizing buffer attributes is not supported.");Z(U.buffer,X,K),U.version=X.version}}return{get:W,remove:H,update:Y}}var RX=`#ifdef USE_ALPHAHASH
	if ( diffuseColor.a < getAlphaHashThreshold( vPosition ) ) discard;
#endif`,kX=`#ifdef USE_ALPHAHASH
	const float ALPHA_HASH_SCALE = 0.05;
	float hash2D( vec2 value ) {
		return fract( 1.0e4 * sin( 17.0 * value.x + 0.1 * value.y ) * ( 0.1 + abs( sin( 13.0 * value.y + value.x ) ) ) );
	}
	float hash3D( vec3 value ) {
		return hash2D( vec2( hash2D( value.xy ), value.z ) );
	}
	float getAlphaHashThreshold( vec3 position ) {
		float maxDeriv = max(
			length( dFdx( position.xyz ) ),
			length( dFdy( position.xyz ) )
		);
		float pixScale = 1.0 / ( ALPHA_HASH_SCALE * maxDeriv );
		vec2 pixScales = vec2(
			exp2( floor( log2( pixScale ) ) ),
			exp2( ceil( log2( pixScale ) ) )
		);
		vec2 alpha = vec2(
			hash3D( floor( pixScales.x * position.xyz ) ),
			hash3D( floor( pixScales.y * position.xyz ) )
		);
		float lerpFactor = fract( log2( pixScale ) );
		float x = ( 1.0 - lerpFactor ) * alpha.x + lerpFactor * alpha.y;
		float a = min( lerpFactor, 1.0 - lerpFactor );
		vec3 cases = vec3(
			x * x / ( 2.0 * a * ( 1.0 - a ) ),
			( x - 0.5 * a ) / ( 1.0 - a ),
			1.0 - ( ( 1.0 - x ) * ( 1.0 - x ) / ( 2.0 * a * ( 1.0 - a ) ) )
		);
		float threshold = ( x < ( 1.0 - a ) )
			? ( ( x < a ) ? cases.x : cases.y )
			: cases.z;
		return clamp( threshold , 1.0e-6, 1.0 );
	}
#endif`,MX=`#ifdef USE_ALPHAMAP
	diffuseColor.a *= texture2D( alphaMap, vAlphaMapUv ).g;
#endif`,DX=`#ifdef USE_ALPHAMAP
	uniform sampler2D alphaMap;
#endif`,LX=`#ifdef USE_ALPHATEST
	#ifdef ALPHA_TO_COVERAGE
	diffuseColor.a = smoothstep( alphaTest, alphaTest + fwidth( diffuseColor.a ), diffuseColor.a );
	if ( diffuseColor.a == 0.0 ) discard;
	#else
	if ( diffuseColor.a < alphaTest ) discard;
	#endif
#endif`,VX=`#ifdef USE_ALPHATEST
	uniform float alphaTest;
#endif`,zX=`#ifdef USE_AOMAP
	float ambientOcclusion = ( texture2D( aoMap, vAoMapUv ).r - 1.0 ) * aoMapIntensity + 1.0;
	reflectedLight.indirectDiffuse *= ambientOcclusion;
	#if defined( USE_CLEARCOAT ) 
		clearcoatSpecularIndirect *= ambientOcclusion;
	#endif
	#if defined( USE_SHEEN ) 
		sheenSpecularIndirect *= ambientOcclusion;
	#endif
	#if defined( USE_ENVMAP ) && defined( STANDARD )
		float dotNV = saturate( dot( geometryNormal, geometryViewDir ) );
		reflectedLight.indirectSpecular *= computeSpecularOcclusion( dotNV, ambientOcclusion, material.roughness );
	#endif
#endif`,BX=`#ifdef USE_AOMAP
	uniform sampler2D aoMap;
	uniform float aoMapIntensity;
#endif`,CX=`#ifdef USE_BATCHING
	#if ! defined( GL_ANGLE_multi_draw )
	#define gl_DrawID _gl_DrawID
	uniform int _gl_DrawID;
	#endif
	uniform highp sampler2D batchingTexture;
	uniform highp usampler2D batchingIdTexture;
	mat4 getBatchingMatrix( const in float i ) {
		int size = textureSize( batchingTexture, 0 ).x;
		int j = int( i ) * 4;
		int x = j % size;
		int y = j / size;
		vec4 v1 = texelFetch( batchingTexture, ivec2( x, y ), 0 );
		vec4 v2 = texelFetch( batchingTexture, ivec2( x + 1, y ), 0 );
		vec4 v3 = texelFetch( batchingTexture, ivec2( x + 2, y ), 0 );
		vec4 v4 = texelFetch( batchingTexture, ivec2( x + 3, y ), 0 );
		return mat4( v1, v2, v3, v4 );
	}
	float getIndirectIndex( const in int i ) {
		int size = textureSize( batchingIdTexture, 0 ).x;
		int x = i % size;
		int y = i / size;
		return float( texelFetch( batchingIdTexture, ivec2( x, y ), 0 ).r );
	}
#endif
#ifdef USE_BATCHING_COLOR
	uniform sampler2D batchingColorTexture;
	vec3 getBatchingColor( const in float i ) {
		int size = textureSize( batchingColorTexture, 0 ).x;
		int j = int( i );
		int x = j % size;
		int y = j / size;
		return texelFetch( batchingColorTexture, ivec2( x, y ), 0 ).rgb;
	}
#endif`,wX=`#ifdef USE_BATCHING
	mat4 batchingMatrix = getBatchingMatrix( getIndirectIndex( gl_DrawID ) );
#endif`,_X=`vec3 transformed = vec3( position );
#ifdef USE_ALPHAHASH
	vPosition = vec3( position );
#endif`,IX=`vec3 objectNormal = vec3( normal );
#ifdef USE_TANGENT
	vec3 objectTangent = vec3( tangent.xyz );
#endif`,PX=`float G_BlinnPhong_Implicit( ) {
	return 0.25;
}
float D_BlinnPhong( const in float shininess, const in float dotNH ) {
	return RECIPROCAL_PI * ( shininess * 0.5 + 1.0 ) * pow( dotNH, shininess );
}
vec3 BRDF_BlinnPhong( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in vec3 specularColor, const in float shininess ) {
	vec3 halfDir = normalize( lightDir + viewDir );
	float dotNH = saturate( dot( normal, halfDir ) );
	float dotVH = saturate( dot( viewDir, halfDir ) );
	vec3 F = F_Schlick( specularColor, 1.0, dotVH );
	float G = G_BlinnPhong_Implicit( );
	float D = D_BlinnPhong( shininess, dotNH );
	return F * ( G * D );
} // validated`,TX=`#ifdef USE_IRIDESCENCE
	const mat3 XYZ_TO_REC709 = mat3(
		 3.2404542, -0.9692660,  0.0556434,
		-1.5371385,  1.8760108, -0.2040259,
		-0.4985314,  0.0415560,  1.0572252
	);
	vec3 Fresnel0ToIor( vec3 fresnel0 ) {
		vec3 sqrtF0 = sqrt( fresnel0 );
		return ( vec3( 1.0 ) + sqrtF0 ) / ( vec3( 1.0 ) - sqrtF0 );
	}
	vec3 IorToFresnel0( vec3 transmittedIor, float incidentIor ) {
		return pow2( ( transmittedIor - vec3( incidentIor ) ) / ( transmittedIor + vec3( incidentIor ) ) );
	}
	float IorToFresnel0( float transmittedIor, float incidentIor ) {
		return pow2( ( transmittedIor - incidentIor ) / ( transmittedIor + incidentIor ));
	}
	vec3 evalSensitivity( float OPD, vec3 shift ) {
		float phase = 2.0 * PI * OPD * 1.0e-9;
		vec3 val = vec3( 5.4856e-13, 4.4201e-13, 5.2481e-13 );
		vec3 pos = vec3( 1.6810e+06, 1.7953e+06, 2.2084e+06 );
		vec3 var = vec3( 4.3278e+09, 9.3046e+09, 6.6121e+09 );
		vec3 xyz = val * sqrt( 2.0 * PI * var ) * cos( pos * phase + shift ) * exp( - pow2( phase ) * var );
		xyz.x += 9.7470e-14 * sqrt( 2.0 * PI * 4.5282e+09 ) * cos( 2.2399e+06 * phase + shift[ 0 ] ) * exp( - 4.5282e+09 * pow2( phase ) );
		xyz /= 1.0685e-7;
		vec3 rgb = XYZ_TO_REC709 * xyz;
		return rgb;
	}
	vec3 evalIridescence( float outsideIOR, float eta2, float cosTheta1, float thinFilmThickness, vec3 baseF0 ) {
		vec3 I;
		float iridescenceIOR = mix( outsideIOR, eta2, smoothstep( 0.0, 0.03, thinFilmThickness ) );
		float sinTheta2Sq = pow2( outsideIOR / iridescenceIOR ) * ( 1.0 - pow2( cosTheta1 ) );
		float cosTheta2Sq = 1.0 - sinTheta2Sq;
		if ( cosTheta2Sq < 0.0 ) {
			return vec3( 1.0 );
		}
		float cosTheta2 = sqrt( cosTheta2Sq );
		float R0 = IorToFresnel0( iridescenceIOR, outsideIOR );
		float R12 = F_Schlick( R0, 1.0, cosTheta1 );
		float T121 = 1.0 - R12;
		float phi12 = 0.0;
		if ( iridescenceIOR < outsideIOR ) phi12 = PI;
		float phi21 = PI - phi12;
		vec3 baseIOR = Fresnel0ToIor( clamp( baseF0, 0.0, 0.9999 ) );		vec3 R1 = IorToFresnel0( baseIOR, iridescenceIOR );
		vec3 R23 = F_Schlick( R1, 1.0, cosTheta2 );
		vec3 phi23 = vec3( 0.0 );
		if ( baseIOR[ 0 ] < iridescenceIOR ) phi23[ 0 ] = PI;
		if ( baseIOR[ 1 ] < iridescenceIOR ) phi23[ 1 ] = PI;
		if ( baseIOR[ 2 ] < iridescenceIOR ) phi23[ 2 ] = PI;
		float OPD = 2.0 * iridescenceIOR * thinFilmThickness * cosTheta2;
		vec3 phi = vec3( phi21 ) + phi23;
		vec3 R123 = clamp( R12 * R23, 1e-5, 0.9999 );
		vec3 r123 = sqrt( R123 );
		vec3 Rs = pow2( T121 ) * R23 / ( vec3( 1.0 ) - R123 );
		vec3 C0 = R12 + Rs;
		I = C0;
		vec3 Cm = Rs - T121;
		for ( int m = 1; m <= 2; ++ m ) {
			Cm *= r123;
			vec3 Sm = 2.0 * evalSensitivity( float( m ) * OPD, float( m ) * phi );
			I += Cm * Sm;
		}
		return max( I, vec3( 0.0 ) );
	}
#endif`,AX=`#ifdef USE_BUMPMAP
	uniform sampler2D bumpMap;
	uniform float bumpScale;
	vec2 dHdxy_fwd() {
		vec2 dSTdx = dFdx( vBumpMapUv );
		vec2 dSTdy = dFdy( vBumpMapUv );
		float Hll = bumpScale * texture2D( bumpMap, vBumpMapUv ).x;
		float dBx = bumpScale * texture2D( bumpMap, vBumpMapUv + dSTdx ).x - Hll;
		float dBy = bumpScale * texture2D( bumpMap, vBumpMapUv + dSTdy ).x - Hll;
		return vec2( dBx, dBy );
	}
	vec3 perturbNormalArb( vec3 surf_pos, vec3 surf_norm, vec2 dHdxy, float faceDirection ) {
		vec3 vSigmaX = normalize( dFdx( surf_pos.xyz ) );
		vec3 vSigmaY = normalize( dFdy( surf_pos.xyz ) );
		vec3 vN = surf_norm;
		vec3 R1 = cross( vSigmaY, vN );
		vec3 R2 = cross( vN, vSigmaX );
		float fDet = dot( vSigmaX, R1 ) * faceDirection;
		vec3 vGrad = sign( fDet ) * ( dHdxy.x * R1 + dHdxy.y * R2 );
		return normalize( abs( fDet ) * surf_norm - vGrad );
	}
#endif`,SX=`#if NUM_CLIPPING_PLANES > 0
	vec4 plane;
	#ifdef ALPHA_TO_COVERAGE
		float distanceToPlane, distanceGradient;
		float clipOpacity = 1.0;
		#pragma unroll_loop_start
		for ( int i = 0; i < UNION_CLIPPING_PLANES; i ++ ) {
			plane = clippingPlanes[ i ];
			distanceToPlane = - dot( vClipPosition, plane.xyz ) + plane.w;
			distanceGradient = fwidth( distanceToPlane ) / 2.0;
			clipOpacity *= smoothstep( - distanceGradient, distanceGradient, distanceToPlane );
			if ( clipOpacity == 0.0 ) discard;
		}
		#pragma unroll_loop_end
		#if UNION_CLIPPING_PLANES < NUM_CLIPPING_PLANES
			float unionClipOpacity = 1.0;
			#pragma unroll_loop_start
			for ( int i = UNION_CLIPPING_PLANES; i < NUM_CLIPPING_PLANES; i ++ ) {
				plane = clippingPlanes[ i ];
				distanceToPlane = - dot( vClipPosition, plane.xyz ) + plane.w;
				distanceGradient = fwidth( distanceToPlane ) / 2.0;
				unionClipOpacity *= 1.0 - smoothstep( - distanceGradient, distanceGradient, distanceToPlane );
			}
			#pragma unroll_loop_end
			clipOpacity *= 1.0 - unionClipOpacity;
		#endif
		diffuseColor.a *= clipOpacity;
		if ( diffuseColor.a == 0.0 ) discard;
	#else
		#pragma unroll_loop_start
		for ( int i = 0; i < UNION_CLIPPING_PLANES; i ++ ) {
			plane = clippingPlanes[ i ];
			if ( dot( vClipPosition, plane.xyz ) > plane.w ) discard;
		}
		#pragma unroll_loop_end
		#if UNION_CLIPPING_PLANES < NUM_CLIPPING_PLANES
			bool clipped = true;
			#pragma unroll_loop_start
			for ( int i = UNION_CLIPPING_PLANES; i < NUM_CLIPPING_PLANES; i ++ ) {
				plane = clippingPlanes[ i ];
				clipped = ( dot( vClipPosition, plane.xyz ) > plane.w ) && clipped;
			}
			#pragma unroll_loop_end
			if ( clipped ) discard;
		#endif
	#endif
#endif`,jX=`#if NUM_CLIPPING_PLANES > 0
	varying vec3 vClipPosition;
	uniform vec4 clippingPlanes[ NUM_CLIPPING_PLANES ];
#endif`,yX=`#if NUM_CLIPPING_PLANES > 0
	varying vec3 vClipPosition;
#endif`,vX=`#if NUM_CLIPPING_PLANES > 0
	vClipPosition = - mvPosition.xyz;
#endif`,fX=`#if defined( USE_COLOR_ALPHA )
	diffuseColor *= vColor;
#elif defined( USE_COLOR )
	diffuseColor.rgb *= vColor;
#endif`,hX=`#if defined( USE_COLOR_ALPHA )
	varying vec4 vColor;
#elif defined( USE_COLOR )
	varying vec3 vColor;
#endif`,bX=`#if defined( USE_COLOR_ALPHA )
	varying vec4 vColor;
#elif defined( USE_COLOR ) || defined( USE_INSTANCING_COLOR ) || defined( USE_BATCHING_COLOR )
	varying vec3 vColor;
#endif`,xX=`#if defined( USE_COLOR_ALPHA )
	vColor = vec4( 1.0 );
#elif defined( USE_COLOR ) || defined( USE_INSTANCING_COLOR ) || defined( USE_BATCHING_COLOR )
	vColor = vec3( 1.0 );
#endif
#ifdef USE_COLOR
	vColor *= color;
#endif
#ifdef USE_INSTANCING_COLOR
	vColor.xyz *= instanceColor.xyz;
#endif
#ifdef USE_BATCHING_COLOR
	vec3 batchingColor = getBatchingColor( getIndirectIndex( gl_DrawID ) );
	vColor.xyz *= batchingColor.xyz;
#endif`,gX=`#define PI 3.141592653589793
#define PI2 6.283185307179586
#define PI_HALF 1.5707963267948966
#define RECIPROCAL_PI 0.3183098861837907
#define RECIPROCAL_PI2 0.15915494309189535
#define EPSILON 1e-6
#ifndef saturate
#define saturate( a ) clamp( a, 0.0, 1.0 )
#endif
#define whiteComplement( a ) ( 1.0 - saturate( a ) )
float pow2( const in float x ) { return x*x; }
vec3 pow2( const in vec3 x ) { return x*x; }
float pow3( const in float x ) { return x*x*x; }
float pow4( const in float x ) { float x2 = x*x; return x2*x2; }
float max3( const in vec3 v ) { return max( max( v.x, v.y ), v.z ); }
float average( const in vec3 v ) { return dot( v, vec3( 0.3333333 ) ); }
highp float rand( const in vec2 uv ) {
	const highp float a = 12.9898, b = 78.233, c = 43758.5453;
	highp float dt = dot( uv.xy, vec2( a,b ) ), sn = mod( dt, PI );
	return fract( sin( sn ) * c );
}
#ifdef HIGH_PRECISION
	float precisionSafeLength( vec3 v ) { return length( v ); }
#else
	float precisionSafeLength( vec3 v ) {
		float maxComponent = max3( abs( v ) );
		return length( v / maxComponent ) * maxComponent;
	}
#endif
struct IncidentLight {
	vec3 color;
	vec3 direction;
	bool visible;
};
struct ReflectedLight {
	vec3 directDiffuse;
	vec3 directSpecular;
	vec3 indirectDiffuse;
	vec3 indirectSpecular;
};
#ifdef USE_ALPHAHASH
	varying vec3 vPosition;
#endif
vec3 transformDirection( in vec3 dir, in mat4 matrix ) {
	return normalize( ( matrix * vec4( dir, 0.0 ) ).xyz );
}
vec3 inverseTransformDirection( in vec3 dir, in mat4 matrix ) {
	return normalize( ( vec4( dir, 0.0 ) * matrix ).xyz );
}
mat3 transposeMat3( const in mat3 m ) {
	mat3 tmp;
	tmp[ 0 ] = vec3( m[ 0 ].x, m[ 1 ].x, m[ 2 ].x );
	tmp[ 1 ] = vec3( m[ 0 ].y, m[ 1 ].y, m[ 2 ].y );
	tmp[ 2 ] = vec3( m[ 0 ].z, m[ 1 ].z, m[ 2 ].z );
	return tmp;
}
bool isPerspectiveMatrix( mat4 m ) {
	return m[ 2 ][ 3 ] == - 1.0;
}
vec2 equirectUv( in vec3 dir ) {
	float u = atan( dir.z, dir.x ) * RECIPROCAL_PI2 + 0.5;
	float v = asin( clamp( dir.y, - 1.0, 1.0 ) ) * RECIPROCAL_PI + 0.5;
	return vec2( u, v );
}
vec3 BRDF_Lambert( const in vec3 diffuseColor ) {
	return RECIPROCAL_PI * diffuseColor;
}
vec3 F_Schlick( const in vec3 f0, const in float f90, const in float dotVH ) {
	float fresnel = exp2( ( - 5.55473 * dotVH - 6.98316 ) * dotVH );
	return f0 * ( 1.0 - fresnel ) + ( f90 * fresnel );
}
float F_Schlick( const in float f0, const in float f90, const in float dotVH ) {
	float fresnel = exp2( ( - 5.55473 * dotVH - 6.98316 ) * dotVH );
	return f0 * ( 1.0 - fresnel ) + ( f90 * fresnel );
} // validated`,pX=`#ifdef ENVMAP_TYPE_CUBE_UV
	#define cubeUV_minMipLevel 4.0
	#define cubeUV_minTileSize 16.0
	float getFace( vec3 direction ) {
		vec3 absDirection = abs( direction );
		float face = - 1.0;
		if ( absDirection.x > absDirection.z ) {
			if ( absDirection.x > absDirection.y )
				face = direction.x > 0.0 ? 0.0 : 3.0;
			else
				face = direction.y > 0.0 ? 1.0 : 4.0;
		} else {
			if ( absDirection.z > absDirection.y )
				face = direction.z > 0.0 ? 2.0 : 5.0;
			else
				face = direction.y > 0.0 ? 1.0 : 4.0;
		}
		return face;
	}
	vec2 getUV( vec3 direction, float face ) {
		vec2 uv;
		if ( face == 0.0 ) {
			uv = vec2( direction.z, direction.y ) / abs( direction.x );
		} else if ( face == 1.0 ) {
			uv = vec2( - direction.x, - direction.z ) / abs( direction.y );
		} else if ( face == 2.0 ) {
			uv = vec2( - direction.x, direction.y ) / abs( direction.z );
		} else if ( face == 3.0 ) {
			uv = vec2( - direction.z, direction.y ) / abs( direction.x );
		} else if ( face == 4.0 ) {
			uv = vec2( - direction.x, direction.z ) / abs( direction.y );
		} else {
			uv = vec2( direction.x, direction.y ) / abs( direction.z );
		}
		return 0.5 * ( uv + 1.0 );
	}
	vec3 bilinearCubeUV( sampler2D envMap, vec3 direction, float mipInt ) {
		float face = getFace( direction );
		float filterInt = max( cubeUV_minMipLevel - mipInt, 0.0 );
		mipInt = max( mipInt, cubeUV_minMipLevel );
		float faceSize = exp2( mipInt );
		highp vec2 uv = getUV( direction, face ) * ( faceSize - 2.0 ) + 1.0;
		if ( face > 2.0 ) {
			uv.y += faceSize;
			face -= 3.0;
		}
		uv.x += face * faceSize;
		uv.x += filterInt * 3.0 * cubeUV_minTileSize;
		uv.y += 4.0 * ( exp2( CUBEUV_MAX_MIP ) - faceSize );
		uv.x *= CUBEUV_TEXEL_WIDTH;
		uv.y *= CUBEUV_TEXEL_HEIGHT;
		#ifdef texture2DGradEXT
			return texture2DGradEXT( envMap, uv, vec2( 0.0 ), vec2( 0.0 ) ).rgb;
		#else
			return texture2D( envMap, uv ).rgb;
		#endif
	}
	#define cubeUV_r0 1.0
	#define cubeUV_m0 - 2.0
	#define cubeUV_r1 0.8
	#define cubeUV_m1 - 1.0
	#define cubeUV_r4 0.4
	#define cubeUV_m4 2.0
	#define cubeUV_r5 0.305
	#define cubeUV_m5 3.0
	#define cubeUV_r6 0.21
	#define cubeUV_m6 4.0
	float roughnessToMip( float roughness ) {
		float mip = 0.0;
		if ( roughness >= cubeUV_r1 ) {
			mip = ( cubeUV_r0 - roughness ) * ( cubeUV_m1 - cubeUV_m0 ) / ( cubeUV_r0 - cubeUV_r1 ) + cubeUV_m0;
		} else if ( roughness >= cubeUV_r4 ) {
			mip = ( cubeUV_r1 - roughness ) * ( cubeUV_m4 - cubeUV_m1 ) / ( cubeUV_r1 - cubeUV_r4 ) + cubeUV_m1;
		} else if ( roughness >= cubeUV_r5 ) {
			mip = ( cubeUV_r4 - roughness ) * ( cubeUV_m5 - cubeUV_m4 ) / ( cubeUV_r4 - cubeUV_r5 ) + cubeUV_m4;
		} else if ( roughness >= cubeUV_r6 ) {
			mip = ( cubeUV_r5 - roughness ) * ( cubeUV_m6 - cubeUV_m5 ) / ( cubeUV_r5 - cubeUV_r6 ) + cubeUV_m5;
		} else {
			mip = - 2.0 * log2( 1.16 * roughness );		}
		return mip;
	}
	vec4 textureCubeUV( sampler2D envMap, vec3 sampleDir, float roughness ) {
		float mip = clamp( roughnessToMip( roughness ), cubeUV_m0, CUBEUV_MAX_MIP );
		float mipF = fract( mip );
		float mipInt = floor( mip );
		vec3 color0 = bilinearCubeUV( envMap, sampleDir, mipInt );
		if ( mipF == 0.0 ) {
			return vec4( color0, 1.0 );
		} else {
			vec3 color1 = bilinearCubeUV( envMap, sampleDir, mipInt + 1.0 );
			return vec4( mix( color0, color1, mipF ), 1.0 );
		}
	}
#endif`,lX=`vec3 transformedNormal = objectNormal;
#ifdef USE_TANGENT
	vec3 transformedTangent = objectTangent;
#endif
#ifdef USE_BATCHING
	mat3 bm = mat3( batchingMatrix );
	transformedNormal /= vec3( dot( bm[ 0 ], bm[ 0 ] ), dot( bm[ 1 ], bm[ 1 ] ), dot( bm[ 2 ], bm[ 2 ] ) );
	transformedNormal = bm * transformedNormal;
	#ifdef USE_TANGENT
		transformedTangent = bm * transformedTangent;
	#endif
#endif
#ifdef USE_INSTANCING
	mat3 im = mat3( instanceMatrix );
	transformedNormal /= vec3( dot( im[ 0 ], im[ 0 ] ), dot( im[ 1 ], im[ 1 ] ), dot( im[ 2 ], im[ 2 ] ) );
	transformedNormal = im * transformedNormal;
	#ifdef USE_TANGENT
		transformedTangent = im * transformedTangent;
	#endif
#endif
transformedNormal = normalMatrix * transformedNormal;
#ifdef FLIP_SIDED
	transformedNormal = - transformedNormal;
#endif
#ifdef USE_TANGENT
	transformedTangent = ( modelViewMatrix * vec4( transformedTangent, 0.0 ) ).xyz;
	#ifdef FLIP_SIDED
		transformedTangent = - transformedTangent;
	#endif
#endif`,dX=`#ifdef USE_DISPLACEMENTMAP
	uniform sampler2D displacementMap;
	uniform float displacementScale;
	uniform float displacementBias;
#endif`,mX=`#ifdef USE_DISPLACEMENTMAP
	transformed += normalize( objectNormal ) * ( texture2D( displacementMap, vDisplacementMapUv ).x * displacementScale + displacementBias );
#endif`,uX=`#ifdef USE_EMISSIVEMAP
	vec4 emissiveColor = texture2D( emissiveMap, vEmissiveMapUv );
	#ifdef DECODE_VIDEO_TEXTURE_EMISSIVE
		emissiveColor = sRGBTransferEOTF( emissiveColor );
	#endif
	totalEmissiveRadiance *= emissiveColor.rgb;
#endif`,cX=`#ifdef USE_EMISSIVEMAP
	uniform sampler2D emissiveMap;
#endif`,nX="gl_FragColor = linearToOutputTexel( gl_FragColor );",sX=`vec4 LinearTransferOETF( in vec4 value ) {
	return value;
}
vec4 sRGBTransferEOTF( in vec4 value ) {
	return vec4( mix( pow( value.rgb * 0.9478672986 + vec3( 0.0521327014 ), vec3( 2.4 ) ), value.rgb * 0.0773993808, vec3( lessThanEqual( value.rgb, vec3( 0.04045 ) ) ) ), value.a );
}
vec4 sRGBTransferOETF( in vec4 value ) {
	return vec4( mix( pow( value.rgb, vec3( 0.41666 ) ) * 1.055 - vec3( 0.055 ), value.rgb * 12.92, vec3( lessThanEqual( value.rgb, vec3( 0.0031308 ) ) ) ), value.a );
}`,oX=`#ifdef USE_ENVMAP
	#ifdef ENV_WORLDPOS
		vec3 cameraToFrag;
		if ( isOrthographic ) {
			cameraToFrag = normalize( vec3( - viewMatrix[ 0 ][ 2 ], - viewMatrix[ 1 ][ 2 ], - viewMatrix[ 2 ][ 2 ] ) );
		} else {
			cameraToFrag = normalize( vWorldPosition - cameraPosition );
		}
		vec3 worldNormal = inverseTransformDirection( normal, viewMatrix );
		#ifdef ENVMAP_MODE_REFLECTION
			vec3 reflectVec = reflect( cameraToFrag, worldNormal );
		#else
			vec3 reflectVec = refract( cameraToFrag, worldNormal, refractionRatio );
		#endif
	#else
		vec3 reflectVec = vReflect;
	#endif
	#ifdef ENVMAP_TYPE_CUBE
		vec4 envColor = textureCube( envMap, envMapRotation * vec3( flipEnvMap * reflectVec.x, reflectVec.yz ) );
	#else
		vec4 envColor = vec4( 0.0 );
	#endif
	#ifdef ENVMAP_BLENDING_MULTIPLY
		outgoingLight = mix( outgoingLight, outgoingLight * envColor.xyz, specularStrength * reflectivity );
	#elif defined( ENVMAP_BLENDING_MIX )
		outgoingLight = mix( outgoingLight, envColor.xyz, specularStrength * reflectivity );
	#elif defined( ENVMAP_BLENDING_ADD )
		outgoingLight += envColor.xyz * specularStrength * reflectivity;
	#endif
#endif`,iX=`#ifdef USE_ENVMAP
	uniform float envMapIntensity;
	uniform float flipEnvMap;
	uniform mat3 envMapRotation;
	#ifdef ENVMAP_TYPE_CUBE
		uniform samplerCube envMap;
	#else
		uniform sampler2D envMap;
	#endif
	
#endif`,aX=`#ifdef USE_ENVMAP
	uniform float reflectivity;
	#if defined( USE_BUMPMAP ) || defined( USE_NORMALMAP ) || defined( PHONG ) || defined( LAMBERT )
		#define ENV_WORLDPOS
	#endif
	#ifdef ENV_WORLDPOS
		varying vec3 vWorldPosition;
		uniform float refractionRatio;
	#else
		varying vec3 vReflect;
	#endif
#endif`,rX=`#ifdef USE_ENVMAP
	#if defined( USE_BUMPMAP ) || defined( USE_NORMALMAP ) || defined( PHONG ) || defined( LAMBERT )
		#define ENV_WORLDPOS
	#endif
	#ifdef ENV_WORLDPOS
		
		varying vec3 vWorldPosition;
	#else
		varying vec3 vReflect;
		uniform float refractionRatio;
	#endif
#endif`,tX=`#ifdef USE_ENVMAP
	#ifdef ENV_WORLDPOS
		vWorldPosition = worldPosition.xyz;
	#else
		vec3 cameraToVertex;
		if ( isOrthographic ) {
			cameraToVertex = normalize( vec3( - viewMatrix[ 0 ][ 2 ], - viewMatrix[ 1 ][ 2 ], - viewMatrix[ 2 ][ 2 ] ) );
		} else {
			cameraToVertex = normalize( worldPosition.xyz - cameraPosition );
		}
		vec3 worldNormal = inverseTransformDirection( transformedNormal, viewMatrix );
		#ifdef ENVMAP_MODE_REFLECTION
			vReflect = reflect( cameraToVertex, worldNormal );
		#else
			vReflect = refract( cameraToVertex, worldNormal, refractionRatio );
		#endif
	#endif
#endif`,eX=`#ifdef USE_FOG
	vFogDepth = - mvPosition.z;
#endif`,JK=`#ifdef USE_FOG
	varying float vFogDepth;
#endif`,QK=`#ifdef USE_FOG
	#ifdef FOG_EXP2
		float fogFactor = 1.0 - exp( - fogDensity * fogDensity * vFogDepth * vFogDepth );
	#else
		float fogFactor = smoothstep( fogNear, fogFar, vFogDepth );
	#endif
	gl_FragColor.rgb = mix( gl_FragColor.rgb, fogColor, fogFactor );
#endif`,$K=`#ifdef USE_FOG
	uniform vec3 fogColor;
	varying float vFogDepth;
	#ifdef FOG_EXP2
		uniform float fogDensity;
	#else
		uniform float fogNear;
		uniform float fogFar;
	#endif
#endif`,ZK=`#ifdef USE_GRADIENTMAP
	uniform sampler2D gradientMap;
#endif
vec3 getGradientIrradiance( vec3 normal, vec3 lightDirection ) {
	float dotNL = dot( normal, lightDirection );
	vec2 coord = vec2( dotNL * 0.5 + 0.5, 0.0 );
	#ifdef USE_GRADIENTMAP
		return vec3( texture2D( gradientMap, coord ).r );
	#else
		vec2 fw = fwidth( coord ) * 0.5;
		return mix( vec3( 0.7 ), vec3( 1.0 ), smoothstep( 0.7 - fw.x, 0.7 + fw.x, coord.x ) );
	#endif
}`,WK=`#ifdef USE_LIGHTMAP
	uniform sampler2D lightMap;
	uniform float lightMapIntensity;
#endif`,HK=`LambertMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.specularStrength = specularStrength;`,YK=`varying vec3 vViewPosition;
struct LambertMaterial {
	vec3 diffuseColor;
	float specularStrength;
};
void RE_Direct_Lambert( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in LambertMaterial material, inout ReflectedLight reflectedLight ) {
	float dotNL = saturate( dot( geometryNormal, directLight.direction ) );
	vec3 irradiance = dotNL * directLight.color;
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
void RE_IndirectDiffuse_Lambert( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in LambertMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
#define RE_Direct				RE_Direct_Lambert
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Lambert`,XK=`uniform bool receiveShadow;
uniform vec3 ambientLightColor;
#if defined( USE_LIGHT_PROBES )
	uniform vec3 lightProbe[ 9 ];
#endif
vec3 shGetIrradianceAt( in vec3 normal, in vec3 shCoefficients[ 9 ] ) {
	float x = normal.x, y = normal.y, z = normal.z;
	vec3 result = shCoefficients[ 0 ] * 0.886227;
	result += shCoefficients[ 1 ] * 2.0 * 0.511664 * y;
	result += shCoefficients[ 2 ] * 2.0 * 0.511664 * z;
	result += shCoefficients[ 3 ] * 2.0 * 0.511664 * x;
	result += shCoefficients[ 4 ] * 2.0 * 0.429043 * x * y;
	result += shCoefficients[ 5 ] * 2.0 * 0.429043 * y * z;
	result += shCoefficients[ 6 ] * ( 0.743125 * z * z - 0.247708 );
	result += shCoefficients[ 7 ] * 2.0 * 0.429043 * x * z;
	result += shCoefficients[ 8 ] * 0.429043 * ( x * x - y * y );
	return result;
}
vec3 getLightProbeIrradiance( const in vec3 lightProbe[ 9 ], const in vec3 normal ) {
	vec3 worldNormal = inverseTransformDirection( normal, viewMatrix );
	vec3 irradiance = shGetIrradianceAt( worldNormal, lightProbe );
	return irradiance;
}
vec3 getAmbientLightIrradiance( const in vec3 ambientLightColor ) {
	vec3 irradiance = ambientLightColor;
	return irradiance;
}
float getDistanceAttenuation( const in float lightDistance, const in float cutoffDistance, const in float decayExponent ) {
	float distanceFalloff = 1.0 / max( pow( lightDistance, decayExponent ), 0.01 );
	if ( cutoffDistance > 0.0 ) {
		distanceFalloff *= pow2( saturate( 1.0 - pow4( lightDistance / cutoffDistance ) ) );
	}
	return distanceFalloff;
}
float getSpotAttenuation( const in float coneCosine, const in float penumbraCosine, const in float angleCosine ) {
	return smoothstep( coneCosine, penumbraCosine, angleCosine );
}
#if NUM_DIR_LIGHTS > 0
	struct DirectionalLight {
		vec3 direction;
		vec3 color;
	};
	uniform DirectionalLight directionalLights[ NUM_DIR_LIGHTS ];
	void getDirectionalLightInfo( const in DirectionalLight directionalLight, out IncidentLight light ) {
		light.color = directionalLight.color;
		light.direction = directionalLight.direction;
		light.visible = true;
	}
#endif
#if NUM_POINT_LIGHTS > 0
	struct PointLight {
		vec3 position;
		vec3 color;
		float distance;
		float decay;
	};
	uniform PointLight pointLights[ NUM_POINT_LIGHTS ];
	void getPointLightInfo( const in PointLight pointLight, const in vec3 geometryPosition, out IncidentLight light ) {
		vec3 lVector = pointLight.position - geometryPosition;
		light.direction = normalize( lVector );
		float lightDistance = length( lVector );
		light.color = pointLight.color;
		light.color *= getDistanceAttenuation( lightDistance, pointLight.distance, pointLight.decay );
		light.visible = ( light.color != vec3( 0.0 ) );
	}
#endif
#if NUM_SPOT_LIGHTS > 0
	struct SpotLight {
		vec3 position;
		vec3 direction;
		vec3 color;
		float distance;
		float decay;
		float coneCos;
		float penumbraCos;
	};
	uniform SpotLight spotLights[ NUM_SPOT_LIGHTS ];
	void getSpotLightInfo( const in SpotLight spotLight, const in vec3 geometryPosition, out IncidentLight light ) {
		vec3 lVector = spotLight.position - geometryPosition;
		light.direction = normalize( lVector );
		float angleCos = dot( light.direction, spotLight.direction );
		float spotAttenuation = getSpotAttenuation( spotLight.coneCos, spotLight.penumbraCos, angleCos );
		if ( spotAttenuation > 0.0 ) {
			float lightDistance = length( lVector );
			light.color = spotLight.color * spotAttenuation;
			light.color *= getDistanceAttenuation( lightDistance, spotLight.distance, spotLight.decay );
			light.visible = ( light.color != vec3( 0.0 ) );
		} else {
			light.color = vec3( 0.0 );
			light.visible = false;
		}
	}
#endif
#if NUM_RECT_AREA_LIGHTS > 0
	struct RectAreaLight {
		vec3 color;
		vec3 position;
		vec3 halfWidth;
		vec3 halfHeight;
	};
	uniform sampler2D ltc_1;	uniform sampler2D ltc_2;
	uniform RectAreaLight rectAreaLights[ NUM_RECT_AREA_LIGHTS ];
#endif
#if NUM_HEMI_LIGHTS > 0
	struct HemisphereLight {
		vec3 direction;
		vec3 skyColor;
		vec3 groundColor;
	};
	uniform HemisphereLight hemisphereLights[ NUM_HEMI_LIGHTS ];
	vec3 getHemisphereLightIrradiance( const in HemisphereLight hemiLight, const in vec3 normal ) {
		float dotNL = dot( normal, hemiLight.direction );
		float hemiDiffuseWeight = 0.5 * dotNL + 0.5;
		vec3 irradiance = mix( hemiLight.groundColor, hemiLight.skyColor, hemiDiffuseWeight );
		return irradiance;
	}
#endif`,KK=`#ifdef USE_ENVMAP
	vec3 getIBLIrradiance( const in vec3 normal ) {
		#ifdef ENVMAP_TYPE_CUBE_UV
			vec3 worldNormal = inverseTransformDirection( normal, viewMatrix );
			vec4 envMapColor = textureCubeUV( envMap, envMapRotation * worldNormal, 1.0 );
			return PI * envMapColor.rgb * envMapIntensity;
		#else
			return vec3( 0.0 );
		#endif
	}
	vec3 getIBLRadiance( const in vec3 viewDir, const in vec3 normal, const in float roughness ) {
		#ifdef ENVMAP_TYPE_CUBE_UV
			vec3 reflectVec = reflect( - viewDir, normal );
			reflectVec = normalize( mix( reflectVec, normal, roughness * roughness) );
			reflectVec = inverseTransformDirection( reflectVec, viewMatrix );
			vec4 envMapColor = textureCubeUV( envMap, envMapRotation * reflectVec, roughness );
			return envMapColor.rgb * envMapIntensity;
		#else
			return vec3( 0.0 );
		#endif
	}
	#ifdef USE_ANISOTROPY
		vec3 getIBLAnisotropyRadiance( const in vec3 viewDir, const in vec3 normal, const in float roughness, const in vec3 bitangent, const in float anisotropy ) {
			#ifdef ENVMAP_TYPE_CUBE_UV
				vec3 bentNormal = cross( bitangent, viewDir );
				bentNormal = normalize( cross( bentNormal, bitangent ) );
				bentNormal = normalize( mix( bentNormal, normal, pow2( pow2( 1.0 - anisotropy * ( 1.0 - roughness ) ) ) ) );
				return getIBLRadiance( viewDir, bentNormal, roughness );
			#else
				return vec3( 0.0 );
			#endif
		}
	#endif
#endif`,UK=`ToonMaterial material;
material.diffuseColor = diffuseColor.rgb;`,GK=`varying vec3 vViewPosition;
struct ToonMaterial {
	vec3 diffuseColor;
};
void RE_Direct_Toon( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in ToonMaterial material, inout ReflectedLight reflectedLight ) {
	vec3 irradiance = getGradientIrradiance( geometryNormal, directLight.direction ) * directLight.color;
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
void RE_IndirectDiffuse_Toon( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in ToonMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
#define RE_Direct				RE_Direct_Toon
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Toon`,qK=`BlinnPhongMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.specularColor = specular;
material.specularShininess = shininess;
material.specularStrength = specularStrength;`,EK=`varying vec3 vViewPosition;
struct BlinnPhongMaterial {
	vec3 diffuseColor;
	vec3 specularColor;
	float specularShininess;
	float specularStrength;
};
void RE_Direct_BlinnPhong( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in BlinnPhongMaterial material, inout ReflectedLight reflectedLight ) {
	float dotNL = saturate( dot( geometryNormal, directLight.direction ) );
	vec3 irradiance = dotNL * directLight.color;
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
	reflectedLight.directSpecular += irradiance * BRDF_BlinnPhong( directLight.direction, geometryViewDir, geometryNormal, material.specularColor, material.specularShininess ) * material.specularStrength;
}
void RE_IndirectDiffuse_BlinnPhong( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in BlinnPhongMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
#define RE_Direct				RE_Direct_BlinnPhong
#define RE_IndirectDiffuse		RE_IndirectDiffuse_BlinnPhong`,NK=`PhysicalMaterial material;
material.diffuseColor = diffuseColor.rgb * ( 1.0 - metalnessFactor );
vec3 dxy = max( abs( dFdx( nonPerturbedNormal ) ), abs( dFdy( nonPerturbedNormal ) ) );
float geometryRoughness = max( max( dxy.x, dxy.y ), dxy.z );
material.roughness = max( roughnessFactor, 0.0525 );material.roughness += geometryRoughness;
material.roughness = min( material.roughness, 1.0 );
#ifdef IOR
	material.ior = ior;
	#ifdef USE_SPECULAR
		float specularIntensityFactor = specularIntensity;
		vec3 specularColorFactor = specularColor;
		#ifdef USE_SPECULAR_COLORMAP
			specularColorFactor *= texture2D( specularColorMap, vSpecularColorMapUv ).rgb;
		#endif
		#ifdef USE_SPECULAR_INTENSITYMAP
			specularIntensityFactor *= texture2D( specularIntensityMap, vSpecularIntensityMapUv ).a;
		#endif
		material.specularF90 = mix( specularIntensityFactor, 1.0, metalnessFactor );
	#else
		float specularIntensityFactor = 1.0;
		vec3 specularColorFactor = vec3( 1.0 );
		material.specularF90 = 1.0;
	#endif
	material.specularColor = mix( min( pow2( ( material.ior - 1.0 ) / ( material.ior + 1.0 ) ) * specularColorFactor, vec3( 1.0 ) ) * specularIntensityFactor, diffuseColor.rgb, metalnessFactor );
#else
	material.specularColor = mix( vec3( 0.04 ), diffuseColor.rgb, metalnessFactor );
	material.specularF90 = 1.0;
#endif
#ifdef USE_CLEARCOAT
	material.clearcoat = clearcoat;
	material.clearcoatRoughness = clearcoatRoughness;
	material.clearcoatF0 = vec3( 0.04 );
	material.clearcoatF90 = 1.0;
	#ifdef USE_CLEARCOATMAP
		material.clearcoat *= texture2D( clearcoatMap, vClearcoatMapUv ).x;
	#endif
	#ifdef USE_CLEARCOAT_ROUGHNESSMAP
		material.clearcoatRoughness *= texture2D( clearcoatRoughnessMap, vClearcoatRoughnessMapUv ).y;
	#endif
	material.clearcoat = saturate( material.clearcoat );	material.clearcoatRoughness = max( material.clearcoatRoughness, 0.0525 );
	material.clearcoatRoughness += geometryRoughness;
	material.clearcoatRoughness = min( material.clearcoatRoughness, 1.0 );
#endif
#ifdef USE_DISPERSION
	material.dispersion = dispersion;
#endif
#ifdef USE_IRIDESCENCE
	material.iridescence = iridescence;
	material.iridescenceIOR = iridescenceIOR;
	#ifdef USE_IRIDESCENCEMAP
		material.iridescence *= texture2D( iridescenceMap, vIridescenceMapUv ).r;
	#endif
	#ifdef USE_IRIDESCENCE_THICKNESSMAP
		material.iridescenceThickness = (iridescenceThicknessMaximum - iridescenceThicknessMinimum) * texture2D( iridescenceThicknessMap, vIridescenceThicknessMapUv ).g + iridescenceThicknessMinimum;
	#else
		material.iridescenceThickness = iridescenceThicknessMaximum;
	#endif
#endif
#ifdef USE_SHEEN
	material.sheenColor = sheenColor;
	#ifdef USE_SHEEN_COLORMAP
		material.sheenColor *= texture2D( sheenColorMap, vSheenColorMapUv ).rgb;
	#endif
	material.sheenRoughness = clamp( sheenRoughness, 0.07, 1.0 );
	#ifdef USE_SHEEN_ROUGHNESSMAP
		material.sheenRoughness *= texture2D( sheenRoughnessMap, vSheenRoughnessMapUv ).a;
	#endif
#endif
#ifdef USE_ANISOTROPY
	#ifdef USE_ANISOTROPYMAP
		mat2 anisotropyMat = mat2( anisotropyVector.x, anisotropyVector.y, - anisotropyVector.y, anisotropyVector.x );
		vec3 anisotropyPolar = texture2D( anisotropyMap, vAnisotropyMapUv ).rgb;
		vec2 anisotropyV = anisotropyMat * normalize( 2.0 * anisotropyPolar.rg - vec2( 1.0 ) ) * anisotropyPolar.b;
	#else
		vec2 anisotropyV = anisotropyVector;
	#endif
	material.anisotropy = length( anisotropyV );
	if( material.anisotropy == 0.0 ) {
		anisotropyV = vec2( 1.0, 0.0 );
	} else {
		anisotropyV /= material.anisotropy;
		material.anisotropy = saturate( material.anisotropy );
	}
	material.alphaT = mix( pow2( material.roughness ), 1.0, pow2( material.anisotropy ) );
	material.anisotropyT = tbn[ 0 ] * anisotropyV.x + tbn[ 1 ] * anisotropyV.y;
	material.anisotropyB = tbn[ 1 ] * anisotropyV.x - tbn[ 0 ] * anisotropyV.y;
#endif`,OK=`struct PhysicalMaterial {
	vec3 diffuseColor;
	float roughness;
	vec3 specularColor;
	float specularF90;
	float dispersion;
	#ifdef USE_CLEARCOAT
		float clearcoat;
		float clearcoatRoughness;
		vec3 clearcoatF0;
		float clearcoatF90;
	#endif
	#ifdef USE_IRIDESCENCE
		float iridescence;
		float iridescenceIOR;
		float iridescenceThickness;
		vec3 iridescenceFresnel;
		vec3 iridescenceF0;
	#endif
	#ifdef USE_SHEEN
		vec3 sheenColor;
		float sheenRoughness;
	#endif
	#ifdef IOR
		float ior;
	#endif
	#ifdef USE_TRANSMISSION
		float transmission;
		float transmissionAlpha;
		float thickness;
		float attenuationDistance;
		vec3 attenuationColor;
	#endif
	#ifdef USE_ANISOTROPY
		float anisotropy;
		float alphaT;
		vec3 anisotropyT;
		vec3 anisotropyB;
	#endif
};
vec3 clearcoatSpecularDirect = vec3( 0.0 );
vec3 clearcoatSpecularIndirect = vec3( 0.0 );
vec3 sheenSpecularDirect = vec3( 0.0 );
vec3 sheenSpecularIndirect = vec3(0.0 );
vec3 Schlick_to_F0( const in vec3 f, const in float f90, const in float dotVH ) {
    float x = clamp( 1.0 - dotVH, 0.0, 1.0 );
    float x2 = x * x;
    float x5 = clamp( x * x2 * x2, 0.0, 0.9999 );
    return ( f - vec3( f90 ) * x5 ) / ( 1.0 - x5 );
}
float V_GGX_SmithCorrelated( const in float alpha, const in float dotNL, const in float dotNV ) {
	float a2 = pow2( alpha );
	float gv = dotNL * sqrt( a2 + ( 1.0 - a2 ) * pow2( dotNV ) );
	float gl = dotNV * sqrt( a2 + ( 1.0 - a2 ) * pow2( dotNL ) );
	return 0.5 / max( gv + gl, EPSILON );
}
float D_GGX( const in float alpha, const in float dotNH ) {
	float a2 = pow2( alpha );
	float denom = pow2( dotNH ) * ( a2 - 1.0 ) + 1.0;
	return RECIPROCAL_PI * a2 / pow2( denom );
}
#ifdef USE_ANISOTROPY
	float V_GGX_SmithCorrelated_Anisotropic( const in float alphaT, const in float alphaB, const in float dotTV, const in float dotBV, const in float dotTL, const in float dotBL, const in float dotNV, const in float dotNL ) {
		float gv = dotNL * length( vec3( alphaT * dotTV, alphaB * dotBV, dotNV ) );
		float gl = dotNV * length( vec3( alphaT * dotTL, alphaB * dotBL, dotNL ) );
		float v = 0.5 / ( gv + gl );
		return saturate(v);
	}
	float D_GGX_Anisotropic( const in float alphaT, const in float alphaB, const in float dotNH, const in float dotTH, const in float dotBH ) {
		float a2 = alphaT * alphaB;
		highp vec3 v = vec3( alphaB * dotTH, alphaT * dotBH, a2 * dotNH );
		highp float v2 = dot( v, v );
		float w2 = a2 / v2;
		return RECIPROCAL_PI * a2 * pow2 ( w2 );
	}
#endif
#ifdef USE_CLEARCOAT
	vec3 BRDF_GGX_Clearcoat( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in PhysicalMaterial material) {
		vec3 f0 = material.clearcoatF0;
		float f90 = material.clearcoatF90;
		float roughness = material.clearcoatRoughness;
		float alpha = pow2( roughness );
		vec3 halfDir = normalize( lightDir + viewDir );
		float dotNL = saturate( dot( normal, lightDir ) );
		float dotNV = saturate( dot( normal, viewDir ) );
		float dotNH = saturate( dot( normal, halfDir ) );
		float dotVH = saturate( dot( viewDir, halfDir ) );
		vec3 F = F_Schlick( f0, f90, dotVH );
		float V = V_GGX_SmithCorrelated( alpha, dotNL, dotNV );
		float D = D_GGX( alpha, dotNH );
		return F * ( V * D );
	}
#endif
vec3 BRDF_GGX( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in PhysicalMaterial material ) {
	vec3 f0 = material.specularColor;
	float f90 = material.specularF90;
	float roughness = material.roughness;
	float alpha = pow2( roughness );
	vec3 halfDir = normalize( lightDir + viewDir );
	float dotNL = saturate( dot( normal, lightDir ) );
	float dotNV = saturate( dot( normal, viewDir ) );
	float dotNH = saturate( dot( normal, halfDir ) );
	float dotVH = saturate( dot( viewDir, halfDir ) );
	vec3 F = F_Schlick( f0, f90, dotVH );
	#ifdef USE_IRIDESCENCE
		F = mix( F, material.iridescenceFresnel, material.iridescence );
	#endif
	#ifdef USE_ANISOTROPY
		float dotTL = dot( material.anisotropyT, lightDir );
		float dotTV = dot( material.anisotropyT, viewDir );
		float dotTH = dot( material.anisotropyT, halfDir );
		float dotBL = dot( material.anisotropyB, lightDir );
		float dotBV = dot( material.anisotropyB, viewDir );
		float dotBH = dot( material.anisotropyB, halfDir );
		float V = V_GGX_SmithCorrelated_Anisotropic( material.alphaT, alpha, dotTV, dotBV, dotTL, dotBL, dotNV, dotNL );
		float D = D_GGX_Anisotropic( material.alphaT, alpha, dotNH, dotTH, dotBH );
	#else
		float V = V_GGX_SmithCorrelated( alpha, dotNL, dotNV );
		float D = D_GGX( alpha, dotNH );
	#endif
	return F * ( V * D );
}
vec2 LTC_Uv( const in vec3 N, const in vec3 V, const in float roughness ) {
	const float LUT_SIZE = 64.0;
	const float LUT_SCALE = ( LUT_SIZE - 1.0 ) / LUT_SIZE;
	const float LUT_BIAS = 0.5 / LUT_SIZE;
	float dotNV = saturate( dot( N, V ) );
	vec2 uv = vec2( roughness, sqrt( 1.0 - dotNV ) );
	uv = uv * LUT_SCALE + LUT_BIAS;
	return uv;
}
float LTC_ClippedSphereFormFactor( const in vec3 f ) {
	float l = length( f );
	return max( ( l * l + f.z ) / ( l + 1.0 ), 0.0 );
}
vec3 LTC_EdgeVectorFormFactor( const in vec3 v1, const in vec3 v2 ) {
	float x = dot( v1, v2 );
	float y = abs( x );
	float a = 0.8543985 + ( 0.4965155 + 0.0145206 * y ) * y;
	float b = 3.4175940 + ( 4.1616724 + y ) * y;
	float v = a / b;
	float theta_sintheta = ( x > 0.0 ) ? v : 0.5 * inversesqrt( max( 1.0 - x * x, 1e-7 ) ) - v;
	return cross( v1, v2 ) * theta_sintheta;
}
vec3 LTC_Evaluate( const in vec3 N, const in vec3 V, const in vec3 P, const in mat3 mInv, const in vec3 rectCoords[ 4 ] ) {
	vec3 v1 = rectCoords[ 1 ] - rectCoords[ 0 ];
	vec3 v2 = rectCoords[ 3 ] - rectCoords[ 0 ];
	vec3 lightNormal = cross( v1, v2 );
	if( dot( lightNormal, P - rectCoords[ 0 ] ) < 0.0 ) return vec3( 0.0 );
	vec3 T1, T2;
	T1 = normalize( V - N * dot( V, N ) );
	T2 = - cross( N, T1 );
	mat3 mat = mInv * transposeMat3( mat3( T1, T2, N ) );
	vec3 coords[ 4 ];
	coords[ 0 ] = mat * ( rectCoords[ 0 ] - P );
	coords[ 1 ] = mat * ( rectCoords[ 1 ] - P );
	coords[ 2 ] = mat * ( rectCoords[ 2 ] - P );
	coords[ 3 ] = mat * ( rectCoords[ 3 ] - P );
	coords[ 0 ] = normalize( coords[ 0 ] );
	coords[ 1 ] = normalize( coords[ 1 ] );
	coords[ 2 ] = normalize( coords[ 2 ] );
	coords[ 3 ] = normalize( coords[ 3 ] );
	vec3 vectorFormFactor = vec3( 0.0 );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 0 ], coords[ 1 ] );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 1 ], coords[ 2 ] );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 2 ], coords[ 3 ] );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 3 ], coords[ 0 ] );
	float result = LTC_ClippedSphereFormFactor( vectorFormFactor );
	return vec3( result );
}
#if defined( USE_SHEEN )
float D_Charlie( float roughness, float dotNH ) {
	float alpha = pow2( roughness );
	float invAlpha = 1.0 / alpha;
	float cos2h = dotNH * dotNH;
	float sin2h = max( 1.0 - cos2h, 0.0078125 );
	return ( 2.0 + invAlpha ) * pow( sin2h, invAlpha * 0.5 ) / ( 2.0 * PI );
}
float V_Neubelt( float dotNV, float dotNL ) {
	return saturate( 1.0 / ( 4.0 * ( dotNL + dotNV - dotNL * dotNV ) ) );
}
vec3 BRDF_Sheen( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, vec3 sheenColor, const in float sheenRoughness ) {
	vec3 halfDir = normalize( lightDir + viewDir );
	float dotNL = saturate( dot( normal, lightDir ) );
	float dotNV = saturate( dot( normal, viewDir ) );
	float dotNH = saturate( dot( normal, halfDir ) );
	float D = D_Charlie( sheenRoughness, dotNH );
	float V = V_Neubelt( dotNV, dotNL );
	return sheenColor * ( D * V );
}
#endif
float IBLSheenBRDF( const in vec3 normal, const in vec3 viewDir, const in float roughness ) {
	float dotNV = saturate( dot( normal, viewDir ) );
	float r2 = roughness * roughness;
	float a = roughness < 0.25 ? -339.2 * r2 + 161.4 * roughness - 25.9 : -8.48 * r2 + 14.3 * roughness - 9.95;
	float b = roughness < 0.25 ? 44.0 * r2 - 23.7 * roughness + 3.26 : 1.97 * r2 - 3.27 * roughness + 0.72;
	float DG = exp( a * dotNV + b ) + ( roughness < 0.25 ? 0.0 : 0.1 * ( roughness - 0.25 ) );
	return saturate( DG * RECIPROCAL_PI );
}
vec2 DFGApprox( const in vec3 normal, const in vec3 viewDir, const in float roughness ) {
	float dotNV = saturate( dot( normal, viewDir ) );
	const vec4 c0 = vec4( - 1, - 0.0275, - 0.572, 0.022 );
	const vec4 c1 = vec4( 1, 0.0425, 1.04, - 0.04 );
	vec4 r = roughness * c0 + c1;
	float a004 = min( r.x * r.x, exp2( - 9.28 * dotNV ) ) * r.x + r.y;
	vec2 fab = vec2( - 1.04, 1.04 ) * a004 + r.zw;
	return fab;
}
vec3 EnvironmentBRDF( const in vec3 normal, const in vec3 viewDir, const in vec3 specularColor, const in float specularF90, const in float roughness ) {
	vec2 fab = DFGApprox( normal, viewDir, roughness );
	return specularColor * fab.x + specularF90 * fab.y;
}
#ifdef USE_IRIDESCENCE
void computeMultiscatteringIridescence( const in vec3 normal, const in vec3 viewDir, const in vec3 specularColor, const in float specularF90, const in float iridescence, const in vec3 iridescenceF0, const in float roughness, inout vec3 singleScatter, inout vec3 multiScatter ) {
#else
void computeMultiscattering( const in vec3 normal, const in vec3 viewDir, const in vec3 specularColor, const in float specularF90, const in float roughness, inout vec3 singleScatter, inout vec3 multiScatter ) {
#endif
	vec2 fab = DFGApprox( normal, viewDir, roughness );
	#ifdef USE_IRIDESCENCE
		vec3 Fr = mix( specularColor, iridescenceF0, iridescence );
	#else
		vec3 Fr = specularColor;
	#endif
	vec3 FssEss = Fr * fab.x + specularF90 * fab.y;
	float Ess = fab.x + fab.y;
	float Ems = 1.0 - Ess;
	vec3 Favg = Fr + ( 1.0 - Fr ) * 0.047619;	vec3 Fms = FssEss * Favg / ( 1.0 - Ems * Favg );
	singleScatter += FssEss;
	multiScatter += Fms * Ems;
}
#if NUM_RECT_AREA_LIGHTS > 0
	void RE_Direct_RectArea_Physical( const in RectAreaLight rectAreaLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
		vec3 normal = geometryNormal;
		vec3 viewDir = geometryViewDir;
		vec3 position = geometryPosition;
		vec3 lightPos = rectAreaLight.position;
		vec3 halfWidth = rectAreaLight.halfWidth;
		vec3 halfHeight = rectAreaLight.halfHeight;
		vec3 lightColor = rectAreaLight.color;
		float roughness = material.roughness;
		vec3 rectCoords[ 4 ];
		rectCoords[ 0 ] = lightPos + halfWidth - halfHeight;		rectCoords[ 1 ] = lightPos - halfWidth - halfHeight;
		rectCoords[ 2 ] = lightPos - halfWidth + halfHeight;
		rectCoords[ 3 ] = lightPos + halfWidth + halfHeight;
		vec2 uv = LTC_Uv( normal, viewDir, roughness );
		vec4 t1 = texture2D( ltc_1, uv );
		vec4 t2 = texture2D( ltc_2, uv );
		mat3 mInv = mat3(
			vec3( t1.x, 0, t1.y ),
			vec3(    0, 1,    0 ),
			vec3( t1.z, 0, t1.w )
		);
		vec3 fresnel = ( material.specularColor * t2.x + ( vec3( 1.0 ) - material.specularColor ) * t2.y );
		reflectedLight.directSpecular += lightColor * fresnel * LTC_Evaluate( normal, viewDir, position, mInv, rectCoords );
		reflectedLight.directDiffuse += lightColor * material.diffuseColor * LTC_Evaluate( normal, viewDir, position, mat3( 1.0 ), rectCoords );
	}
#endif
void RE_Direct_Physical( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
	float dotNL = saturate( dot( geometryNormal, directLight.direction ) );
	vec3 irradiance = dotNL * directLight.color;
	#ifdef USE_CLEARCOAT
		float dotNLcc = saturate( dot( geometryClearcoatNormal, directLight.direction ) );
		vec3 ccIrradiance = dotNLcc * directLight.color;
		clearcoatSpecularDirect += ccIrradiance * BRDF_GGX_Clearcoat( directLight.direction, geometryViewDir, geometryClearcoatNormal, material );
	#endif
	#ifdef USE_SHEEN
		sheenSpecularDirect += irradiance * BRDF_Sheen( directLight.direction, geometryViewDir, geometryNormal, material.sheenColor, material.sheenRoughness );
	#endif
	reflectedLight.directSpecular += irradiance * BRDF_GGX( directLight.direction, geometryViewDir, geometryNormal, material );
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
void RE_IndirectDiffuse_Physical( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
void RE_IndirectSpecular_Physical( const in vec3 radiance, const in vec3 irradiance, const in vec3 clearcoatRadiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight) {
	#ifdef USE_CLEARCOAT
		clearcoatSpecularIndirect += clearcoatRadiance * EnvironmentBRDF( geometryClearcoatNormal, geometryViewDir, material.clearcoatF0, material.clearcoatF90, material.clearcoatRoughness );
	#endif
	#ifdef USE_SHEEN
		sheenSpecularIndirect += irradiance * material.sheenColor * IBLSheenBRDF( geometryNormal, geometryViewDir, material.sheenRoughness );
	#endif
	vec3 singleScattering = vec3( 0.0 );
	vec3 multiScattering = vec3( 0.0 );
	vec3 cosineWeightedIrradiance = irradiance * RECIPROCAL_PI;
	#ifdef USE_IRIDESCENCE
		computeMultiscatteringIridescence( geometryNormal, geometryViewDir, material.specularColor, material.specularF90, material.iridescence, material.iridescenceFresnel, material.roughness, singleScattering, multiScattering );
	#else
		computeMultiscattering( geometryNormal, geometryViewDir, material.specularColor, material.specularF90, material.roughness, singleScattering, multiScattering );
	#endif
	vec3 totalScattering = singleScattering + multiScattering;
	vec3 diffuse = material.diffuseColor * ( 1.0 - max( max( totalScattering.r, totalScattering.g ), totalScattering.b ) );
	reflectedLight.indirectSpecular += radiance * singleScattering;
	reflectedLight.indirectSpecular += multiScattering * cosineWeightedIrradiance;
	reflectedLight.indirectDiffuse += diffuse * cosineWeightedIrradiance;
}
#define RE_Direct				RE_Direct_Physical
#define RE_Direct_RectArea		RE_Direct_RectArea_Physical
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Physical
#define RE_IndirectSpecular		RE_IndirectSpecular_Physical
float computeSpecularOcclusion( const in float dotNV, const in float ambientOcclusion, const in float roughness ) {
	return saturate( pow( dotNV + ambientOcclusion, exp2( - 16.0 * roughness - 1.0 ) ) - 1.0 + ambientOcclusion );
}`,FK=`
vec3 geometryPosition = - vViewPosition;
vec3 geometryNormal = normal;
vec3 geometryViewDir = ( isOrthographic ) ? vec3( 0, 0, 1 ) : normalize( vViewPosition );
vec3 geometryClearcoatNormal = vec3( 0.0 );
#ifdef USE_CLEARCOAT
	geometryClearcoatNormal = clearcoatNormal;
#endif
#ifdef USE_IRIDESCENCE
	float dotNVi = saturate( dot( normal, geometryViewDir ) );
	if ( material.iridescenceThickness == 0.0 ) {
		material.iridescence = 0.0;
	} else {
		material.iridescence = saturate( material.iridescence );
	}
	if ( material.iridescence > 0.0 ) {
		material.iridescenceFresnel = evalIridescence( 1.0, material.iridescenceIOR, dotNVi, material.iridescenceThickness, material.specularColor );
		material.iridescenceF0 = Schlick_to_F0( material.iridescenceFresnel, 1.0, dotNVi );
	}
#endif
IncidentLight directLight;
#if ( NUM_POINT_LIGHTS > 0 ) && defined( RE_Direct )
	PointLight pointLight;
	#if defined( USE_SHADOWMAP ) && NUM_POINT_LIGHT_SHADOWS > 0
	PointLightShadow pointLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_POINT_LIGHTS; i ++ ) {
		pointLight = pointLights[ i ];
		getPointLightInfo( pointLight, geometryPosition, directLight );
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_POINT_LIGHT_SHADOWS )
		pointLightShadow = pointLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getPointShadow( pointShadowMap[ i ], pointLightShadow.shadowMapSize, pointLightShadow.shadowIntensity, pointLightShadow.shadowBias, pointLightShadow.shadowRadius, vPointShadowCoord[ i ], pointLightShadow.shadowCameraNear, pointLightShadow.shadowCameraFar ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_SPOT_LIGHTS > 0 ) && defined( RE_Direct )
	SpotLight spotLight;
	vec4 spotColor;
	vec3 spotLightCoord;
	bool inSpotLightMap;
	#if defined( USE_SHADOWMAP ) && NUM_SPOT_LIGHT_SHADOWS > 0
	SpotLightShadow spotLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SPOT_LIGHTS; i ++ ) {
		spotLight = spotLights[ i ];
		getSpotLightInfo( spotLight, geometryPosition, directLight );
		#if ( UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS )
		#define SPOT_LIGHT_MAP_INDEX UNROLLED_LOOP_INDEX
		#elif ( UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS )
		#define SPOT_LIGHT_MAP_INDEX NUM_SPOT_LIGHT_MAPS
		#else
		#define SPOT_LIGHT_MAP_INDEX ( UNROLLED_LOOP_INDEX - NUM_SPOT_LIGHT_SHADOWS + NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS )
		#endif
		#if ( SPOT_LIGHT_MAP_INDEX < NUM_SPOT_LIGHT_MAPS )
			spotLightCoord = vSpotLightCoord[ i ].xyz / vSpotLightCoord[ i ].w;
			inSpotLightMap = all( lessThan( abs( spotLightCoord * 2. - 1. ), vec3( 1.0 ) ) );
			spotColor = texture2D( spotLightMap[ SPOT_LIGHT_MAP_INDEX ], spotLightCoord.xy );
			directLight.color = inSpotLightMap ? directLight.color * spotColor.rgb : directLight.color;
		#endif
		#undef SPOT_LIGHT_MAP_INDEX
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS )
		spotLightShadow = spotLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getShadow( spotShadowMap[ i ], spotLightShadow.shadowMapSize, spotLightShadow.shadowIntensity, spotLightShadow.shadowBias, spotLightShadow.shadowRadius, vSpotLightCoord[ i ] ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_DIR_LIGHTS > 0 ) && defined( RE_Direct )
	DirectionalLight directionalLight;
	#if defined( USE_SHADOWMAP ) && NUM_DIR_LIGHT_SHADOWS > 0
	DirectionalLightShadow directionalLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_DIR_LIGHTS; i ++ ) {
		directionalLight = directionalLights[ i ];
		getDirectionalLightInfo( directionalLight, directLight );
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_DIR_LIGHT_SHADOWS )
		directionalLightShadow = directionalLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getShadow( directionalShadowMap[ i ], directionalLightShadow.shadowMapSize, directionalLightShadow.shadowIntensity, directionalLightShadow.shadowBias, directionalLightShadow.shadowRadius, vDirectionalShadowCoord[ i ] ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_RECT_AREA_LIGHTS > 0 ) && defined( RE_Direct_RectArea )
	RectAreaLight rectAreaLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_RECT_AREA_LIGHTS; i ++ ) {
		rectAreaLight = rectAreaLights[ i ];
		RE_Direct_RectArea( rectAreaLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if defined( RE_IndirectDiffuse )
	vec3 iblIrradiance = vec3( 0.0 );
	vec3 irradiance = getAmbientLightIrradiance( ambientLightColor );
	#if defined( USE_LIGHT_PROBES )
		irradiance += getLightProbeIrradiance( lightProbe, geometryNormal );
	#endif
	#if ( NUM_HEMI_LIGHTS > 0 )
		#pragma unroll_loop_start
		for ( int i = 0; i < NUM_HEMI_LIGHTS; i ++ ) {
			irradiance += getHemisphereLightIrradiance( hemisphereLights[ i ], geometryNormal );
		}
		#pragma unroll_loop_end
	#endif
#endif
#if defined( RE_IndirectSpecular )
	vec3 radiance = vec3( 0.0 );
	vec3 clearcoatRadiance = vec3( 0.0 );
#endif`,RK=`#if defined( RE_IndirectDiffuse )
	#ifdef USE_LIGHTMAP
		vec4 lightMapTexel = texture2D( lightMap, vLightMapUv );
		vec3 lightMapIrradiance = lightMapTexel.rgb * lightMapIntensity;
		irradiance += lightMapIrradiance;
	#endif
	#if defined( USE_ENVMAP ) && defined( STANDARD ) && defined( ENVMAP_TYPE_CUBE_UV )
		iblIrradiance += getIBLIrradiance( geometryNormal );
	#endif
#endif
#if defined( USE_ENVMAP ) && defined( RE_IndirectSpecular )
	#ifdef USE_ANISOTROPY
		radiance += getIBLAnisotropyRadiance( geometryViewDir, geometryNormal, material.roughness, material.anisotropyB, material.anisotropy );
	#else
		radiance += getIBLRadiance( geometryViewDir, geometryNormal, material.roughness );
	#endif
	#ifdef USE_CLEARCOAT
		clearcoatRadiance += getIBLRadiance( geometryViewDir, geometryClearcoatNormal, material.clearcoatRoughness );
	#endif
#endif`,kK=`#if defined( RE_IndirectDiffuse )
	RE_IndirectDiffuse( irradiance, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
#endif
#if defined( RE_IndirectSpecular )
	RE_IndirectSpecular( radiance, iblIrradiance, clearcoatRadiance, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
#endif`,MK=`#if defined( USE_LOGDEPTHBUF )
	gl_FragDepth = vIsPerspective == 0.0 ? gl_FragCoord.z : log2( vFragDepth ) * logDepthBufFC * 0.5;
#endif`,DK=`#if defined( USE_LOGDEPTHBUF )
	uniform float logDepthBufFC;
	varying float vFragDepth;
	varying float vIsPerspective;
#endif`,LK=`#ifdef USE_LOGDEPTHBUF
	varying float vFragDepth;
	varying float vIsPerspective;
#endif`,VK=`#ifdef USE_LOGDEPTHBUF
	vFragDepth = 1.0 + gl_Position.w;
	vIsPerspective = float( isPerspectiveMatrix( projectionMatrix ) );
#endif`,zK=`#ifdef USE_MAP
	vec4 sampledDiffuseColor = texture2D( map, vMapUv );
	#ifdef DECODE_VIDEO_TEXTURE
		sampledDiffuseColor = sRGBTransferEOTF( sampledDiffuseColor );
	#endif
	diffuseColor *= sampledDiffuseColor;
#endif`,BK=`#ifdef USE_MAP
	uniform sampler2D map;
#endif`,CK=`#if defined( USE_MAP ) || defined( USE_ALPHAMAP )
	#if defined( USE_POINTS_UV )
		vec2 uv = vUv;
	#else
		vec2 uv = ( uvTransform * vec3( gl_PointCoord.x, 1.0 - gl_PointCoord.y, 1 ) ).xy;
	#endif
#endif
#ifdef USE_MAP
	diffuseColor *= texture2D( map, uv );
#endif
#ifdef USE_ALPHAMAP
	diffuseColor.a *= texture2D( alphaMap, uv ).g;
#endif`,wK=`#if defined( USE_POINTS_UV )
	varying vec2 vUv;
#else
	#if defined( USE_MAP ) || defined( USE_ALPHAMAP )
		uniform mat3 uvTransform;
	#endif
#endif
#ifdef USE_MAP
	uniform sampler2D map;
#endif
#ifdef USE_ALPHAMAP
	uniform sampler2D alphaMap;
#endif`,_K=`float metalnessFactor = metalness;
#ifdef USE_METALNESSMAP
	vec4 texelMetalness = texture2D( metalnessMap, vMetalnessMapUv );
	metalnessFactor *= texelMetalness.b;
#endif`,IK=`#ifdef USE_METALNESSMAP
	uniform sampler2D metalnessMap;
#endif`,PK=`#ifdef USE_INSTANCING_MORPH
	float morphTargetInfluences[ MORPHTARGETS_COUNT ];
	float morphTargetBaseInfluence = texelFetch( morphTexture, ivec2( 0, gl_InstanceID ), 0 ).r;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		morphTargetInfluences[i] =  texelFetch( morphTexture, ivec2( i + 1, gl_InstanceID ), 0 ).r;
	}
#endif`,TK=`#if defined( USE_MORPHCOLORS )
	vColor *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		#if defined( USE_COLOR_ALPHA )
			if ( morphTargetInfluences[ i ] != 0.0 ) vColor += getMorph( gl_VertexID, i, 2 ) * morphTargetInfluences[ i ];
		#elif defined( USE_COLOR )
			if ( morphTargetInfluences[ i ] != 0.0 ) vColor += getMorph( gl_VertexID, i, 2 ).rgb * morphTargetInfluences[ i ];
		#endif
	}
#endif`,AK=`#ifdef USE_MORPHNORMALS
	objectNormal *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		if ( morphTargetInfluences[ i ] != 0.0 ) objectNormal += getMorph( gl_VertexID, i, 1 ).xyz * morphTargetInfluences[ i ];
	}
#endif`,SK=`#ifdef USE_MORPHTARGETS
	#ifndef USE_INSTANCING_MORPH
		uniform float morphTargetBaseInfluence;
		uniform float morphTargetInfluences[ MORPHTARGETS_COUNT ];
	#endif
	uniform sampler2DArray morphTargetsTexture;
	uniform ivec2 morphTargetsTextureSize;
	vec4 getMorph( const in int vertexIndex, const in int morphTargetIndex, const in int offset ) {
		int texelIndex = vertexIndex * MORPHTARGETS_TEXTURE_STRIDE + offset;
		int y = texelIndex / morphTargetsTextureSize.x;
		int x = texelIndex - y * morphTargetsTextureSize.x;
		ivec3 morphUV = ivec3( x, y, morphTargetIndex );
		return texelFetch( morphTargetsTexture, morphUV, 0 );
	}
#endif`,jK=`#ifdef USE_MORPHTARGETS
	transformed *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		if ( morphTargetInfluences[ i ] != 0.0 ) transformed += getMorph( gl_VertexID, i, 0 ).xyz * morphTargetInfluences[ i ];
	}
#endif`,yK=`float faceDirection = gl_FrontFacing ? 1.0 : - 1.0;
#ifdef FLAT_SHADED
	vec3 fdx = dFdx( vViewPosition );
	vec3 fdy = dFdy( vViewPosition );
	vec3 normal = normalize( cross( fdx, fdy ) );
#else
	vec3 normal = normalize( vNormal );
	#ifdef DOUBLE_SIDED
		normal *= faceDirection;
	#endif
#endif
#if defined( USE_NORMALMAP_TANGENTSPACE ) || defined( USE_CLEARCOAT_NORMALMAP ) || defined( USE_ANISOTROPY )
	#ifdef USE_TANGENT
		mat3 tbn = mat3( normalize( vTangent ), normalize( vBitangent ), normal );
	#else
		mat3 tbn = getTangentFrame( - vViewPosition, normal,
		#if defined( USE_NORMALMAP )
			vNormalMapUv
		#elif defined( USE_CLEARCOAT_NORMALMAP )
			vClearcoatNormalMapUv
		#else
			vUv
		#endif
		);
	#endif
	#if defined( DOUBLE_SIDED ) && ! defined( FLAT_SHADED )
		tbn[0] *= faceDirection;
		tbn[1] *= faceDirection;
	#endif
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	#ifdef USE_TANGENT
		mat3 tbn2 = mat3( normalize( vTangent ), normalize( vBitangent ), normal );
	#else
		mat3 tbn2 = getTangentFrame( - vViewPosition, normal, vClearcoatNormalMapUv );
	#endif
	#if defined( DOUBLE_SIDED ) && ! defined( FLAT_SHADED )
		tbn2[0] *= faceDirection;
		tbn2[1] *= faceDirection;
	#endif
#endif
vec3 nonPerturbedNormal = normal;`,vK=`#ifdef USE_NORMALMAP_OBJECTSPACE
	normal = texture2D( normalMap, vNormalMapUv ).xyz * 2.0 - 1.0;
	#ifdef FLIP_SIDED
		normal = - normal;
	#endif
	#ifdef DOUBLE_SIDED
		normal = normal * faceDirection;
	#endif
	normal = normalize( normalMatrix * normal );
#elif defined( USE_NORMALMAP_TANGENTSPACE )
	vec3 mapN = texture2D( normalMap, vNormalMapUv ).xyz * 2.0 - 1.0;
	mapN.xy *= normalScale;
	normal = normalize( tbn * mapN );
#elif defined( USE_BUMPMAP )
	normal = perturbNormalArb( - vViewPosition, normal, dHdxy_fwd(), faceDirection );
#endif`,fK=`#ifndef FLAT_SHADED
	varying vec3 vNormal;
	#ifdef USE_TANGENT
		varying vec3 vTangent;
		varying vec3 vBitangent;
	#endif
#endif`,hK=`#ifndef FLAT_SHADED
	varying vec3 vNormal;
	#ifdef USE_TANGENT
		varying vec3 vTangent;
		varying vec3 vBitangent;
	#endif
#endif`,bK=`#ifndef FLAT_SHADED
	vNormal = normalize( transformedNormal );
	#ifdef USE_TANGENT
		vTangent = normalize( transformedTangent );
		vBitangent = normalize( cross( vNormal, vTangent ) * tangent.w );
	#endif
#endif`,xK=`#ifdef USE_NORMALMAP
	uniform sampler2D normalMap;
	uniform vec2 normalScale;
#endif
#ifdef USE_NORMALMAP_OBJECTSPACE
	uniform mat3 normalMatrix;
#endif
#if ! defined ( USE_TANGENT ) && ( defined ( USE_NORMALMAP_TANGENTSPACE ) || defined ( USE_CLEARCOAT_NORMALMAP ) || defined( USE_ANISOTROPY ) )
	mat3 getTangentFrame( vec3 eye_pos, vec3 surf_norm, vec2 uv ) {
		vec3 q0 = dFdx( eye_pos.xyz );
		vec3 q1 = dFdy( eye_pos.xyz );
		vec2 st0 = dFdx( uv.st );
		vec2 st1 = dFdy( uv.st );
		vec3 N = surf_norm;
		vec3 q1perp = cross( q1, N );
		vec3 q0perp = cross( N, q0 );
		vec3 T = q1perp * st0.x + q0perp * st1.x;
		vec3 B = q1perp * st0.y + q0perp * st1.y;
		float det = max( dot( T, T ), dot( B, B ) );
		float scale = ( det == 0.0 ) ? 0.0 : inversesqrt( det );
		return mat3( T * scale, B * scale, N );
	}
#endif`,gK=`#ifdef USE_CLEARCOAT
	vec3 clearcoatNormal = nonPerturbedNormal;
#endif`,pK=`#ifdef USE_CLEARCOAT_NORMALMAP
	vec3 clearcoatMapN = texture2D( clearcoatNormalMap, vClearcoatNormalMapUv ).xyz * 2.0 - 1.0;
	clearcoatMapN.xy *= clearcoatNormalScale;
	clearcoatNormal = normalize( tbn2 * clearcoatMapN );
#endif`,lK=`#ifdef USE_CLEARCOATMAP
	uniform sampler2D clearcoatMap;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	uniform sampler2D clearcoatNormalMap;
	uniform vec2 clearcoatNormalScale;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	uniform sampler2D clearcoatRoughnessMap;
#endif`,dK=`#ifdef USE_IRIDESCENCEMAP
	uniform sampler2D iridescenceMap;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	uniform sampler2D iridescenceThicknessMap;
#endif`,mK=`#ifdef OPAQUE
diffuseColor.a = 1.0;
#endif
#ifdef USE_TRANSMISSION
diffuseColor.a *= material.transmissionAlpha;
#endif
gl_FragColor = vec4( outgoingLight, diffuseColor.a );`,uK=`vec3 packNormalToRGB( const in vec3 normal ) {
	return normalize( normal ) * 0.5 + 0.5;
}
vec3 unpackRGBToNormal( const in vec3 rgb ) {
	return 2.0 * rgb.xyz - 1.0;
}
const float PackUpscale = 256. / 255.;const float UnpackDownscale = 255. / 256.;const float ShiftRight8 = 1. / 256.;
const float Inv255 = 1. / 255.;
const vec4 PackFactors = vec4( 1.0, 256.0, 256.0 * 256.0, 256.0 * 256.0 * 256.0 );
const vec2 UnpackFactors2 = vec2( UnpackDownscale, 1.0 / PackFactors.g );
const vec3 UnpackFactors3 = vec3( UnpackDownscale / PackFactors.rg, 1.0 / PackFactors.b );
const vec4 UnpackFactors4 = vec4( UnpackDownscale / PackFactors.rgb, 1.0 / PackFactors.a );
vec4 packDepthToRGBA( const in float v ) {
	if( v <= 0.0 )
		return vec4( 0., 0., 0., 0. );
	if( v >= 1.0 )
		return vec4( 1., 1., 1., 1. );
	float vuf;
	float af = modf( v * PackFactors.a, vuf );
	float bf = modf( vuf * ShiftRight8, vuf );
	float gf = modf( vuf * ShiftRight8, vuf );
	return vec4( vuf * Inv255, gf * PackUpscale, bf * PackUpscale, af );
}
vec3 packDepthToRGB( const in float v ) {
	if( v <= 0.0 )
		return vec3( 0., 0., 0. );
	if( v >= 1.0 )
		return vec3( 1., 1., 1. );
	float vuf;
	float bf = modf( v * PackFactors.b, vuf );
	float gf = modf( vuf * ShiftRight8, vuf );
	return vec3( vuf * Inv255, gf * PackUpscale, bf );
}
vec2 packDepthToRG( const in float v ) {
	if( v <= 0.0 )
		return vec2( 0., 0. );
	if( v >= 1.0 )
		return vec2( 1., 1. );
	float vuf;
	float gf = modf( v * 256., vuf );
	return vec2( vuf * Inv255, gf );
}
float unpackRGBAToDepth( const in vec4 v ) {
	return dot( v, UnpackFactors4 );
}
float unpackRGBToDepth( const in vec3 v ) {
	return dot( v, UnpackFactors3 );
}
float unpackRGToDepth( const in vec2 v ) {
	return v.r * UnpackFactors2.r + v.g * UnpackFactors2.g;
}
vec4 pack2HalfToRGBA( const in vec2 v ) {
	vec4 r = vec4( v.x, fract( v.x * 255.0 ), v.y, fract( v.y * 255.0 ) );
	return vec4( r.x - r.y / 255.0, r.y, r.z - r.w / 255.0, r.w );
}
vec2 unpackRGBATo2Half( const in vec4 v ) {
	return vec2( v.x + ( v.y / 255.0 ), v.z + ( v.w / 255.0 ) );
}
float viewZToOrthographicDepth( const in float viewZ, const in float near, const in float far ) {
	return ( viewZ + near ) / ( near - far );
}
float orthographicDepthToViewZ( const in float depth, const in float near, const in float far ) {
	return depth * ( near - far ) - near;
}
float viewZToPerspectiveDepth( const in float viewZ, const in float near, const in float far ) {
	return ( ( near + viewZ ) * far ) / ( ( far - near ) * viewZ );
}
float perspectiveDepthToViewZ( const in float depth, const in float near, const in float far ) {
	return ( near * far ) / ( ( far - near ) * depth - far );
}`,cK=`#ifdef PREMULTIPLIED_ALPHA
	gl_FragColor.rgb *= gl_FragColor.a;
#endif`,nK=`vec4 mvPosition = vec4( transformed, 1.0 );
#ifdef USE_BATCHING
	mvPosition = batchingMatrix * mvPosition;
#endif
#ifdef USE_INSTANCING
	mvPosition = instanceMatrix * mvPosition;
#endif
mvPosition = modelViewMatrix * mvPosition;
gl_Position = projectionMatrix * mvPosition;`,sK=`#ifdef DITHERING
	gl_FragColor.rgb = dithering( gl_FragColor.rgb );
#endif`,oK=`#ifdef DITHERING
	vec3 dithering( vec3 color ) {
		float grid_position = rand( gl_FragCoord.xy );
		vec3 dither_shift_RGB = vec3( 0.25 / 255.0, -0.25 / 255.0, 0.25 / 255.0 );
		dither_shift_RGB = mix( 2.0 * dither_shift_RGB, -2.0 * dither_shift_RGB, grid_position );
		return color + dither_shift_RGB;
	}
#endif`,iK=`float roughnessFactor = roughness;
#ifdef USE_ROUGHNESSMAP
	vec4 texelRoughness = texture2D( roughnessMap, vRoughnessMapUv );
	roughnessFactor *= texelRoughness.g;
#endif`,aK=`#ifdef USE_ROUGHNESSMAP
	uniform sampler2D roughnessMap;
#endif`,rK=`#if NUM_SPOT_LIGHT_COORDS > 0
	varying vec4 vSpotLightCoord[ NUM_SPOT_LIGHT_COORDS ];
#endif
#if NUM_SPOT_LIGHT_MAPS > 0
	uniform sampler2D spotLightMap[ NUM_SPOT_LIGHT_MAPS ];
#endif
#ifdef USE_SHADOWMAP
	#if NUM_DIR_LIGHT_SHADOWS > 0
		uniform sampler2D directionalShadowMap[ NUM_DIR_LIGHT_SHADOWS ];
		varying vec4 vDirectionalShadowCoord[ NUM_DIR_LIGHT_SHADOWS ];
		struct DirectionalLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform DirectionalLightShadow directionalLightShadows[ NUM_DIR_LIGHT_SHADOWS ];
	#endif
	#if NUM_SPOT_LIGHT_SHADOWS > 0
		uniform sampler2D spotShadowMap[ NUM_SPOT_LIGHT_SHADOWS ];
		struct SpotLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform SpotLightShadow spotLightShadows[ NUM_SPOT_LIGHT_SHADOWS ];
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
		uniform sampler2D pointShadowMap[ NUM_POINT_LIGHT_SHADOWS ];
		varying vec4 vPointShadowCoord[ NUM_POINT_LIGHT_SHADOWS ];
		struct PointLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
			float shadowCameraNear;
			float shadowCameraFar;
		};
		uniform PointLightShadow pointLightShadows[ NUM_POINT_LIGHT_SHADOWS ];
	#endif
	float texture2DCompare( sampler2D depths, vec2 uv, float compare ) {
		float depth = unpackRGBAToDepth( texture2D( depths, uv ) );
		#ifdef USE_REVERSEDEPTHBUF
			return step( depth, compare );
		#else
			return step( compare, depth );
		#endif
	}
	vec2 texture2DDistribution( sampler2D shadow, vec2 uv ) {
		return unpackRGBATo2Half( texture2D( shadow, uv ) );
	}
	float VSMShadow (sampler2D shadow, vec2 uv, float compare ){
		float occlusion = 1.0;
		vec2 distribution = texture2DDistribution( shadow, uv );
		#ifdef USE_REVERSEDEPTHBUF
			float hard_shadow = step( distribution.x, compare );
		#else
			float hard_shadow = step( compare , distribution.x );
		#endif
		if (hard_shadow != 1.0 ) {
			float distance = compare - distribution.x ;
			float variance = max( 0.00000, distribution.y * distribution.y );
			float softness_probability = variance / (variance + distance * distance );			softness_probability = clamp( ( softness_probability - 0.3 ) / ( 0.95 - 0.3 ), 0.0, 1.0 );			occlusion = clamp( max( hard_shadow, softness_probability ), 0.0, 1.0 );
		}
		return occlusion;
	}
	float getShadow( sampler2D shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord ) {
		float shadow = 1.0;
		shadowCoord.xyz /= shadowCoord.w;
		shadowCoord.z += shadowBias;
		bool inFrustum = shadowCoord.x >= 0.0 && shadowCoord.x <= 1.0 && shadowCoord.y >= 0.0 && shadowCoord.y <= 1.0;
		bool frustumTest = inFrustum && shadowCoord.z <= 1.0;
		if ( frustumTest ) {
		#if defined( SHADOWMAP_TYPE_PCF )
			vec2 texelSize = vec2( 1.0 ) / shadowMapSize;
			float dx0 = - texelSize.x * shadowRadius;
			float dy0 = - texelSize.y * shadowRadius;
			float dx1 = + texelSize.x * shadowRadius;
			float dy1 = + texelSize.y * shadowRadius;
			float dx2 = dx0 / 2.0;
			float dy2 = dy0 / 2.0;
			float dx3 = dx1 / 2.0;
			float dy3 = dy1 / 2.0;
			shadow = (
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx0, dy0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( 0.0, dy0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx1, dy0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx2, dy2 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( 0.0, dy2 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx3, dy2 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx0, 0.0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx2, 0.0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy, shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx3, 0.0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx1, 0.0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx2, dy3 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( 0.0, dy3 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx3, dy3 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx0, dy1 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( 0.0, dy1 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx1, dy1 ), shadowCoord.z )
			) * ( 1.0 / 17.0 );
		#elif defined( SHADOWMAP_TYPE_PCF_SOFT )
			vec2 texelSize = vec2( 1.0 ) / shadowMapSize;
			float dx = texelSize.x;
			float dy = texelSize.y;
			vec2 uv = shadowCoord.xy;
			vec2 f = fract( uv * shadowMapSize + 0.5 );
			uv -= f * texelSize;
			shadow = (
				texture2DCompare( shadowMap, uv, shadowCoord.z ) +
				texture2DCompare( shadowMap, uv + vec2( dx, 0.0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, uv + vec2( 0.0, dy ), shadowCoord.z ) +
				texture2DCompare( shadowMap, uv + texelSize, shadowCoord.z ) +
				mix( texture2DCompare( shadowMap, uv + vec2( -dx, 0.0 ), shadowCoord.z ),
					 texture2DCompare( shadowMap, uv + vec2( 2.0 * dx, 0.0 ), shadowCoord.z ),
					 f.x ) +
				mix( texture2DCompare( shadowMap, uv + vec2( -dx, dy ), shadowCoord.z ),
					 texture2DCompare( shadowMap, uv + vec2( 2.0 * dx, dy ), shadowCoord.z ),
					 f.x ) +
				mix( texture2DCompare( shadowMap, uv + vec2( 0.0, -dy ), shadowCoord.z ),
					 texture2DCompare( shadowMap, uv + vec2( 0.0, 2.0 * dy ), shadowCoord.z ),
					 f.y ) +
				mix( texture2DCompare( shadowMap, uv + vec2( dx, -dy ), shadowCoord.z ),
					 texture2DCompare( shadowMap, uv + vec2( dx, 2.0 * dy ), shadowCoord.z ),
					 f.y ) +
				mix( mix( texture2DCompare( shadowMap, uv + vec2( -dx, -dy ), shadowCoord.z ),
						  texture2DCompare( shadowMap, uv + vec2( 2.0 * dx, -dy ), shadowCoord.z ),
						  f.x ),
					 mix( texture2DCompare( shadowMap, uv + vec2( -dx, 2.0 * dy ), shadowCoord.z ),
						  texture2DCompare( shadowMap, uv + vec2( 2.0 * dx, 2.0 * dy ), shadowCoord.z ),
						  f.x ),
					 f.y )
			) * ( 1.0 / 9.0 );
		#elif defined( SHADOWMAP_TYPE_VSM )
			shadow = VSMShadow( shadowMap, shadowCoord.xy, shadowCoord.z );
		#else
			shadow = texture2DCompare( shadowMap, shadowCoord.xy, shadowCoord.z );
		#endif
		}
		return mix( 1.0, shadow, shadowIntensity );
	}
	vec2 cubeToUV( vec3 v, float texelSizeY ) {
		vec3 absV = abs( v );
		float scaleToCube = 1.0 / max( absV.x, max( absV.y, absV.z ) );
		absV *= scaleToCube;
		v *= scaleToCube * ( 1.0 - 2.0 * texelSizeY );
		vec2 planar = v.xy;
		float almostATexel = 1.5 * texelSizeY;
		float almostOne = 1.0 - almostATexel;
		if ( absV.z >= almostOne ) {
			if ( v.z > 0.0 )
				planar.x = 4.0 - v.x;
		} else if ( absV.x >= almostOne ) {
			float signX = sign( v.x );
			planar.x = v.z * signX + 2.0 * signX;
		} else if ( absV.y >= almostOne ) {
			float signY = sign( v.y );
			planar.x = v.x + 2.0 * signY + 2.0;
			planar.y = v.z * signY - 2.0;
		}
		return vec2( 0.125, 0.25 ) * planar + vec2( 0.375, 0.75 );
	}
	float getPointShadow( sampler2D shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord, float shadowCameraNear, float shadowCameraFar ) {
		float shadow = 1.0;
		vec3 lightToPosition = shadowCoord.xyz;
		
		float lightToPositionLength = length( lightToPosition );
		if ( lightToPositionLength - shadowCameraFar <= 0.0 && lightToPositionLength - shadowCameraNear >= 0.0 ) {
			float dp = ( lightToPositionLength - shadowCameraNear ) / ( shadowCameraFar - shadowCameraNear );			dp += shadowBias;
			vec3 bd3D = normalize( lightToPosition );
			vec2 texelSize = vec2( 1.0 ) / ( shadowMapSize * vec2( 4.0, 2.0 ) );
			#if defined( SHADOWMAP_TYPE_PCF ) || defined( SHADOWMAP_TYPE_PCF_SOFT ) || defined( SHADOWMAP_TYPE_VSM )
				vec2 offset = vec2( - 1, 1 ) * shadowRadius * texelSize.y;
				shadow = (
					texture2DCompare( shadowMap, cubeToUV( bd3D + offset.xyy, texelSize.y ), dp ) +
					texture2DCompare( shadowMap, cubeToUV( bd3D + offset.yyy, texelSize.y ), dp ) +
					texture2DCompare( shadowMap, cubeToUV( bd3D + offset.xyx, texelSize.y ), dp ) +
					texture2DCompare( shadowMap, cubeToUV( bd3D + offset.yyx, texelSize.y ), dp ) +
					texture2DCompare( shadowMap, cubeToUV( bd3D, texelSize.y ), dp ) +
					texture2DCompare( shadowMap, cubeToUV( bd3D + offset.xxy, texelSize.y ), dp ) +
					texture2DCompare( shadowMap, cubeToUV( bd3D + offset.yxy, texelSize.y ), dp ) +
					texture2DCompare( shadowMap, cubeToUV( bd3D + offset.xxx, texelSize.y ), dp ) +
					texture2DCompare( shadowMap, cubeToUV( bd3D + offset.yxx, texelSize.y ), dp )
				) * ( 1.0 / 9.0 );
			#else
				shadow = texture2DCompare( shadowMap, cubeToUV( bd3D, texelSize.y ), dp );
			#endif
		}
		return mix( 1.0, shadow, shadowIntensity );
	}
#endif`,tK=`#if NUM_SPOT_LIGHT_COORDS > 0
	uniform mat4 spotLightMatrix[ NUM_SPOT_LIGHT_COORDS ];
	varying vec4 vSpotLightCoord[ NUM_SPOT_LIGHT_COORDS ];
#endif
#ifdef USE_SHADOWMAP
	#if NUM_DIR_LIGHT_SHADOWS > 0
		uniform mat4 directionalShadowMatrix[ NUM_DIR_LIGHT_SHADOWS ];
		varying vec4 vDirectionalShadowCoord[ NUM_DIR_LIGHT_SHADOWS ];
		struct DirectionalLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform DirectionalLightShadow directionalLightShadows[ NUM_DIR_LIGHT_SHADOWS ];
	#endif
	#if NUM_SPOT_LIGHT_SHADOWS > 0
		struct SpotLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform SpotLightShadow spotLightShadows[ NUM_SPOT_LIGHT_SHADOWS ];
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
		uniform mat4 pointShadowMatrix[ NUM_POINT_LIGHT_SHADOWS ];
		varying vec4 vPointShadowCoord[ NUM_POINT_LIGHT_SHADOWS ];
		struct PointLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
			float shadowCameraNear;
			float shadowCameraFar;
		};
		uniform PointLightShadow pointLightShadows[ NUM_POINT_LIGHT_SHADOWS ];
	#endif
#endif`,eK=`#if ( defined( USE_SHADOWMAP ) && ( NUM_DIR_LIGHT_SHADOWS > 0 || NUM_POINT_LIGHT_SHADOWS > 0 ) ) || ( NUM_SPOT_LIGHT_COORDS > 0 )
	vec3 shadowWorldNormal = inverseTransformDirection( transformedNormal, viewMatrix );
	vec4 shadowWorldPosition;
#endif
#if defined( USE_SHADOWMAP )
	#if NUM_DIR_LIGHT_SHADOWS > 0
		#pragma unroll_loop_start
		for ( int i = 0; i < NUM_DIR_LIGHT_SHADOWS; i ++ ) {
			shadowWorldPosition = worldPosition + vec4( shadowWorldNormal * directionalLightShadows[ i ].shadowNormalBias, 0 );
			vDirectionalShadowCoord[ i ] = directionalShadowMatrix[ i ] * shadowWorldPosition;
		}
		#pragma unroll_loop_end
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
		#pragma unroll_loop_start
		for ( int i = 0; i < NUM_POINT_LIGHT_SHADOWS; i ++ ) {
			shadowWorldPosition = worldPosition + vec4( shadowWorldNormal * pointLightShadows[ i ].shadowNormalBias, 0 );
			vPointShadowCoord[ i ] = pointShadowMatrix[ i ] * shadowWorldPosition;
		}
		#pragma unroll_loop_end
	#endif
#endif
#if NUM_SPOT_LIGHT_COORDS > 0
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SPOT_LIGHT_COORDS; i ++ ) {
		shadowWorldPosition = worldPosition;
		#if ( defined( USE_SHADOWMAP ) && UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS )
			shadowWorldPosition.xyz += shadowWorldNormal * spotLightShadows[ i ].shadowNormalBias;
		#endif
		vSpotLightCoord[ i ] = spotLightMatrix[ i ] * shadowWorldPosition;
	}
	#pragma unroll_loop_end
#endif`,JU=`float getShadowMask() {
	float shadow = 1.0;
	#ifdef USE_SHADOWMAP
	#if NUM_DIR_LIGHT_SHADOWS > 0
	DirectionalLightShadow directionalLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_DIR_LIGHT_SHADOWS; i ++ ) {
		directionalLight = directionalLightShadows[ i ];
		shadow *= receiveShadow ? getShadow( directionalShadowMap[ i ], directionalLight.shadowMapSize, directionalLight.shadowIntensity, directionalLight.shadowBias, directionalLight.shadowRadius, vDirectionalShadowCoord[ i ] ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#if NUM_SPOT_LIGHT_SHADOWS > 0
	SpotLightShadow spotLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SPOT_LIGHT_SHADOWS; i ++ ) {
		spotLight = spotLightShadows[ i ];
		shadow *= receiveShadow ? getShadow( spotShadowMap[ i ], spotLight.shadowMapSize, spotLight.shadowIntensity, spotLight.shadowBias, spotLight.shadowRadius, vSpotLightCoord[ i ] ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
	PointLightShadow pointLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_POINT_LIGHT_SHADOWS; i ++ ) {
		pointLight = pointLightShadows[ i ];
		shadow *= receiveShadow ? getPointShadow( pointShadowMap[ i ], pointLight.shadowMapSize, pointLight.shadowIntensity, pointLight.shadowBias, pointLight.shadowRadius, vPointShadowCoord[ i ], pointLight.shadowCameraNear, pointLight.shadowCameraFar ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#endif
	return shadow;
}`,QU=`#ifdef USE_SKINNING
	mat4 boneMatX = getBoneMatrix( skinIndex.x );
	mat4 boneMatY = getBoneMatrix( skinIndex.y );
	mat4 boneMatZ = getBoneMatrix( skinIndex.z );
	mat4 boneMatW = getBoneMatrix( skinIndex.w );
#endif`,$U=`#ifdef USE_SKINNING
	uniform mat4 bindMatrix;
	uniform mat4 bindMatrixInverse;
	uniform highp sampler2D boneTexture;
	mat4 getBoneMatrix( const in float i ) {
		int size = textureSize( boneTexture, 0 ).x;
		int j = int( i ) * 4;
		int x = j % size;
		int y = j / size;
		vec4 v1 = texelFetch( boneTexture, ivec2( x, y ), 0 );
		vec4 v2 = texelFetch( boneTexture, ivec2( x + 1, y ), 0 );
		vec4 v3 = texelFetch( boneTexture, ivec2( x + 2, y ), 0 );
		vec4 v4 = texelFetch( boneTexture, ivec2( x + 3, y ), 0 );
		return mat4( v1, v2, v3, v4 );
	}
#endif`,ZU=`#ifdef USE_SKINNING
	vec4 skinVertex = bindMatrix * vec4( transformed, 1.0 );
	vec4 skinned = vec4( 0.0 );
	skinned += boneMatX * skinVertex * skinWeight.x;
	skinned += boneMatY * skinVertex * skinWeight.y;
	skinned += boneMatZ * skinVertex * skinWeight.z;
	skinned += boneMatW * skinVertex * skinWeight.w;
	transformed = ( bindMatrixInverse * skinned ).xyz;
#endif`,WU=`#ifdef USE_SKINNING
	mat4 skinMatrix = mat4( 0.0 );
	skinMatrix += skinWeight.x * boneMatX;
	skinMatrix += skinWeight.y * boneMatY;
	skinMatrix += skinWeight.z * boneMatZ;
	skinMatrix += skinWeight.w * boneMatW;
	skinMatrix = bindMatrixInverse * skinMatrix * bindMatrix;
	objectNormal = vec4( skinMatrix * vec4( objectNormal, 0.0 ) ).xyz;
	#ifdef USE_TANGENT
		objectTangent = vec4( skinMatrix * vec4( objectTangent, 0.0 ) ).xyz;
	#endif
#endif`,HU=`float specularStrength;
#ifdef USE_SPECULARMAP
	vec4 texelSpecular = texture2D( specularMap, vSpecularMapUv );
	specularStrength = texelSpecular.r;
#else
	specularStrength = 1.0;
#endif`,YU=`#ifdef USE_SPECULARMAP
	uniform sampler2D specularMap;
#endif`,XU=`#if defined( TONE_MAPPING )
	gl_FragColor.rgb = toneMapping( gl_FragColor.rgb );
#endif`,KU=`#ifndef saturate
#define saturate( a ) clamp( a, 0.0, 1.0 )
#endif
uniform float toneMappingExposure;
vec3 LinearToneMapping( vec3 color ) {
	return saturate( toneMappingExposure * color );
}
vec3 ReinhardToneMapping( vec3 color ) {
	color *= toneMappingExposure;
	return saturate( color / ( vec3( 1.0 ) + color ) );
}
vec3 CineonToneMapping( vec3 color ) {
	color *= toneMappingExposure;
	color = max( vec3( 0.0 ), color - 0.004 );
	return pow( ( color * ( 6.2 * color + 0.5 ) ) / ( color * ( 6.2 * color + 1.7 ) + 0.06 ), vec3( 2.2 ) );
}
vec3 RRTAndODTFit( vec3 v ) {
	vec3 a = v * ( v + 0.0245786 ) - 0.000090537;
	vec3 b = v * ( 0.983729 * v + 0.4329510 ) + 0.238081;
	return a / b;
}
vec3 ACESFilmicToneMapping( vec3 color ) {
	const mat3 ACESInputMat = mat3(
		vec3( 0.59719, 0.07600, 0.02840 ),		vec3( 0.35458, 0.90834, 0.13383 ),
		vec3( 0.04823, 0.01566, 0.83777 )
	);
	const mat3 ACESOutputMat = mat3(
		vec3(  1.60475, -0.10208, -0.00327 ),		vec3( -0.53108,  1.10813, -0.07276 ),
		vec3( -0.07367, -0.00605,  1.07602 )
	);
	color *= toneMappingExposure / 0.6;
	color = ACESInputMat * color;
	color = RRTAndODTFit( color );
	color = ACESOutputMat * color;
	return saturate( color );
}
const mat3 LINEAR_REC2020_TO_LINEAR_SRGB = mat3(
	vec3( 1.6605, - 0.1246, - 0.0182 ),
	vec3( - 0.5876, 1.1329, - 0.1006 ),
	vec3( - 0.0728, - 0.0083, 1.1187 )
);
const mat3 LINEAR_SRGB_TO_LINEAR_REC2020 = mat3(
	vec3( 0.6274, 0.0691, 0.0164 ),
	vec3( 0.3293, 0.9195, 0.0880 ),
	vec3( 0.0433, 0.0113, 0.8956 )
);
vec3 agxDefaultContrastApprox( vec3 x ) {
	vec3 x2 = x * x;
	vec3 x4 = x2 * x2;
	return + 15.5 * x4 * x2
		- 40.14 * x4 * x
		+ 31.96 * x4
		- 6.868 * x2 * x
		+ 0.4298 * x2
		+ 0.1191 * x
		- 0.00232;
}
vec3 AgXToneMapping( vec3 color ) {
	const mat3 AgXInsetMatrix = mat3(
		vec3( 0.856627153315983, 0.137318972929847, 0.11189821299995 ),
		vec3( 0.0951212405381588, 0.761241990602591, 0.0767994186031903 ),
		vec3( 0.0482516061458583, 0.101439036467562, 0.811302368396859 )
	);
	const mat3 AgXOutsetMatrix = mat3(
		vec3( 1.1271005818144368, - 0.1413297634984383, - 0.14132976349843826 ),
		vec3( - 0.11060664309660323, 1.157823702216272, - 0.11060664309660294 ),
		vec3( - 0.016493938717834573, - 0.016493938717834257, 1.2519364065950405 )
	);
	const float AgxMinEv = - 12.47393;	const float AgxMaxEv = 4.026069;
	color *= toneMappingExposure;
	color = LINEAR_SRGB_TO_LINEAR_REC2020 * color;
	color = AgXInsetMatrix * color;
	color = max( color, 1e-10 );	color = log2( color );
	color = ( color - AgxMinEv ) / ( AgxMaxEv - AgxMinEv );
	color = clamp( color, 0.0, 1.0 );
	color = agxDefaultContrastApprox( color );
	color = AgXOutsetMatrix * color;
	color = pow( max( vec3( 0.0 ), color ), vec3( 2.2 ) );
	color = LINEAR_REC2020_TO_LINEAR_SRGB * color;
	color = clamp( color, 0.0, 1.0 );
	return color;
}
vec3 NeutralToneMapping( vec3 color ) {
	const float StartCompression = 0.8 - 0.04;
	const float Desaturation = 0.15;
	color *= toneMappingExposure;
	float x = min( color.r, min( color.g, color.b ) );
	float offset = x < 0.08 ? x - 6.25 * x * x : 0.04;
	color -= offset;
	float peak = max( color.r, max( color.g, color.b ) );
	if ( peak < StartCompression ) return color;
	float d = 1. - StartCompression;
	float newPeak = 1. - d * d / ( peak + d - StartCompression );
	color *= newPeak / peak;
	float g = 1. - 1. / ( Desaturation * ( peak - newPeak ) + 1. );
	return mix( color, vec3( newPeak ), g );
}
vec3 CustomToneMapping( vec3 color ) { return color; }`,UU=`#ifdef USE_TRANSMISSION
	material.transmission = transmission;
	material.transmissionAlpha = 1.0;
	material.thickness = thickness;
	material.attenuationDistance = attenuationDistance;
	material.attenuationColor = attenuationColor;
	#ifdef USE_TRANSMISSIONMAP
		material.transmission *= texture2D( transmissionMap, vTransmissionMapUv ).r;
	#endif
	#ifdef USE_THICKNESSMAP
		material.thickness *= texture2D( thicknessMap, vThicknessMapUv ).g;
	#endif
	vec3 pos = vWorldPosition;
	vec3 v = normalize( cameraPosition - pos );
	vec3 n = inverseTransformDirection( normal, viewMatrix );
	vec4 transmitted = getIBLVolumeRefraction(
		n, v, material.roughness, material.diffuseColor, material.specularColor, material.specularF90,
		pos, modelMatrix, viewMatrix, projectionMatrix, material.dispersion, material.ior, material.thickness,
		material.attenuationColor, material.attenuationDistance );
	material.transmissionAlpha = mix( material.transmissionAlpha, transmitted.a, material.transmission );
	totalDiffuse = mix( totalDiffuse, transmitted.rgb, material.transmission );
#endif`,GU=`#ifdef USE_TRANSMISSION
	uniform float transmission;
	uniform float thickness;
	uniform float attenuationDistance;
	uniform vec3 attenuationColor;
	#ifdef USE_TRANSMISSIONMAP
		uniform sampler2D transmissionMap;
	#endif
	#ifdef USE_THICKNESSMAP
		uniform sampler2D thicknessMap;
	#endif
	uniform vec2 transmissionSamplerSize;
	uniform sampler2D transmissionSamplerMap;
	uniform mat4 modelMatrix;
	uniform mat4 projectionMatrix;
	varying vec3 vWorldPosition;
	float w0( float a ) {
		return ( 1.0 / 6.0 ) * ( a * ( a * ( - a + 3.0 ) - 3.0 ) + 1.0 );
	}
	float w1( float a ) {
		return ( 1.0 / 6.0 ) * ( a *  a * ( 3.0 * a - 6.0 ) + 4.0 );
	}
	float w2( float a ){
		return ( 1.0 / 6.0 ) * ( a * ( a * ( - 3.0 * a + 3.0 ) + 3.0 ) + 1.0 );
	}
	float w3( float a ) {
		return ( 1.0 / 6.0 ) * ( a * a * a );
	}
	float g0( float a ) {
		return w0( a ) + w1( a );
	}
	float g1( float a ) {
		return w2( a ) + w3( a );
	}
	float h0( float a ) {
		return - 1.0 + w1( a ) / ( w0( a ) + w1( a ) );
	}
	float h1( float a ) {
		return 1.0 + w3( a ) / ( w2( a ) + w3( a ) );
	}
	vec4 bicubic( sampler2D tex, vec2 uv, vec4 texelSize, float lod ) {
		uv = uv * texelSize.zw + 0.5;
		vec2 iuv = floor( uv );
		vec2 fuv = fract( uv );
		float g0x = g0( fuv.x );
		float g1x = g1( fuv.x );
		float h0x = h0( fuv.x );
		float h1x = h1( fuv.x );
		float h0y = h0( fuv.y );
		float h1y = h1( fuv.y );
		vec2 p0 = ( vec2( iuv.x + h0x, iuv.y + h0y ) - 0.5 ) * texelSize.xy;
		vec2 p1 = ( vec2( iuv.x + h1x, iuv.y + h0y ) - 0.5 ) * texelSize.xy;
		vec2 p2 = ( vec2( iuv.x + h0x, iuv.y + h1y ) - 0.5 ) * texelSize.xy;
		vec2 p3 = ( vec2( iuv.x + h1x, iuv.y + h1y ) - 0.5 ) * texelSize.xy;
		return g0( fuv.y ) * ( g0x * textureLod( tex, p0, lod ) + g1x * textureLod( tex, p1, lod ) ) +
			g1( fuv.y ) * ( g0x * textureLod( tex, p2, lod ) + g1x * textureLod( tex, p3, lod ) );
	}
	vec4 textureBicubic( sampler2D sampler, vec2 uv, float lod ) {
		vec2 fLodSize = vec2( textureSize( sampler, int( lod ) ) );
		vec2 cLodSize = vec2( textureSize( sampler, int( lod + 1.0 ) ) );
		vec2 fLodSizeInv = 1.0 / fLodSize;
		vec2 cLodSizeInv = 1.0 / cLodSize;
		vec4 fSample = bicubic( sampler, uv, vec4( fLodSizeInv, fLodSize ), floor( lod ) );
		vec4 cSample = bicubic( sampler, uv, vec4( cLodSizeInv, cLodSize ), ceil( lod ) );
		return mix( fSample, cSample, fract( lod ) );
	}
	vec3 getVolumeTransmissionRay( const in vec3 n, const in vec3 v, const in float thickness, const in float ior, const in mat4 modelMatrix ) {
		vec3 refractionVector = refract( - v, normalize( n ), 1.0 / ior );
		vec3 modelScale;
		modelScale.x = length( vec3( modelMatrix[ 0 ].xyz ) );
		modelScale.y = length( vec3( modelMatrix[ 1 ].xyz ) );
		modelScale.z = length( vec3( modelMatrix[ 2 ].xyz ) );
		return normalize( refractionVector ) * thickness * modelScale;
	}
	float applyIorToRoughness( const in float roughness, const in float ior ) {
		return roughness * clamp( ior * 2.0 - 2.0, 0.0, 1.0 );
	}
	vec4 getTransmissionSample( const in vec2 fragCoord, const in float roughness, const in float ior ) {
		float lod = log2( transmissionSamplerSize.x ) * applyIorToRoughness( roughness, ior );
		return textureBicubic( transmissionSamplerMap, fragCoord.xy, lod );
	}
	vec3 volumeAttenuation( const in float transmissionDistance, const in vec3 attenuationColor, const in float attenuationDistance ) {
		if ( isinf( attenuationDistance ) ) {
			return vec3( 1.0 );
		} else {
			vec3 attenuationCoefficient = -log( attenuationColor ) / attenuationDistance;
			vec3 transmittance = exp( - attenuationCoefficient * transmissionDistance );			return transmittance;
		}
	}
	vec4 getIBLVolumeRefraction( const in vec3 n, const in vec3 v, const in float roughness, const in vec3 diffuseColor,
		const in vec3 specularColor, const in float specularF90, const in vec3 position, const in mat4 modelMatrix,
		const in mat4 viewMatrix, const in mat4 projMatrix, const in float dispersion, const in float ior, const in float thickness,
		const in vec3 attenuationColor, const in float attenuationDistance ) {
		vec4 transmittedLight;
		vec3 transmittance;
		#ifdef USE_DISPERSION
			float halfSpread = ( ior - 1.0 ) * 0.025 * dispersion;
			vec3 iors = vec3( ior - halfSpread, ior, ior + halfSpread );
			for ( int i = 0; i < 3; i ++ ) {
				vec3 transmissionRay = getVolumeTransmissionRay( n, v, thickness, iors[ i ], modelMatrix );
				vec3 refractedRayExit = position + transmissionRay;
				vec4 ndcPos = projMatrix * viewMatrix * vec4( refractedRayExit, 1.0 );
				vec2 refractionCoords = ndcPos.xy / ndcPos.w;
				refractionCoords += 1.0;
				refractionCoords /= 2.0;
				vec4 transmissionSample = getTransmissionSample( refractionCoords, roughness, iors[ i ] );
				transmittedLight[ i ] = transmissionSample[ i ];
				transmittedLight.a += transmissionSample.a;
				transmittance[ i ] = diffuseColor[ i ] * volumeAttenuation( length( transmissionRay ), attenuationColor, attenuationDistance )[ i ];
			}
			transmittedLight.a /= 3.0;
		#else
			vec3 transmissionRay = getVolumeTransmissionRay( n, v, thickness, ior, modelMatrix );
			vec3 refractedRayExit = position + transmissionRay;
			vec4 ndcPos = projMatrix * viewMatrix * vec4( refractedRayExit, 1.0 );
			vec2 refractionCoords = ndcPos.xy / ndcPos.w;
			refractionCoords += 1.0;
			refractionCoords /= 2.0;
			transmittedLight = getTransmissionSample( refractionCoords, roughness, ior );
			transmittance = diffuseColor * volumeAttenuation( length( transmissionRay ), attenuationColor, attenuationDistance );
		#endif
		vec3 attenuatedColor = transmittance * transmittedLight.rgb;
		vec3 F = EnvironmentBRDF( n, v, specularColor, specularF90, roughness );
		float transmittanceFactor = ( transmittance.r + transmittance.g + transmittance.b ) / 3.0;
		return vec4( ( 1.0 - F ) * attenuatedColor, 1.0 - ( 1.0 - transmittedLight.a ) * transmittanceFactor );
	}
#endif`,qU=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
	varying vec2 vUv;
#endif
#ifdef USE_MAP
	varying vec2 vMapUv;
#endif
#ifdef USE_ALPHAMAP
	varying vec2 vAlphaMapUv;
#endif
#ifdef USE_LIGHTMAP
	varying vec2 vLightMapUv;
#endif
#ifdef USE_AOMAP
	varying vec2 vAoMapUv;
#endif
#ifdef USE_BUMPMAP
	varying vec2 vBumpMapUv;
#endif
#ifdef USE_NORMALMAP
	varying vec2 vNormalMapUv;
#endif
#ifdef USE_EMISSIVEMAP
	varying vec2 vEmissiveMapUv;
#endif
#ifdef USE_METALNESSMAP
	varying vec2 vMetalnessMapUv;
#endif
#ifdef USE_ROUGHNESSMAP
	varying vec2 vRoughnessMapUv;
#endif
#ifdef USE_ANISOTROPYMAP
	varying vec2 vAnisotropyMapUv;
#endif
#ifdef USE_CLEARCOATMAP
	varying vec2 vClearcoatMapUv;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	varying vec2 vClearcoatNormalMapUv;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	varying vec2 vClearcoatRoughnessMapUv;
#endif
#ifdef USE_IRIDESCENCEMAP
	varying vec2 vIridescenceMapUv;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	varying vec2 vIridescenceThicknessMapUv;
#endif
#ifdef USE_SHEEN_COLORMAP
	varying vec2 vSheenColorMapUv;
#endif
#ifdef USE_SHEEN_ROUGHNESSMAP
	varying vec2 vSheenRoughnessMapUv;
#endif
#ifdef USE_SPECULARMAP
	varying vec2 vSpecularMapUv;
#endif
#ifdef USE_SPECULAR_COLORMAP
	varying vec2 vSpecularColorMapUv;
#endif
#ifdef USE_SPECULAR_INTENSITYMAP
	varying vec2 vSpecularIntensityMapUv;
#endif
#ifdef USE_TRANSMISSIONMAP
	uniform mat3 transmissionMapTransform;
	varying vec2 vTransmissionMapUv;
#endif
#ifdef USE_THICKNESSMAP
	uniform mat3 thicknessMapTransform;
	varying vec2 vThicknessMapUv;
#endif`,EU=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
	varying vec2 vUv;
#endif
#ifdef USE_MAP
	uniform mat3 mapTransform;
	varying vec2 vMapUv;
#endif
#ifdef USE_ALPHAMAP
	uniform mat3 alphaMapTransform;
	varying vec2 vAlphaMapUv;
#endif
#ifdef USE_LIGHTMAP
	uniform mat3 lightMapTransform;
	varying vec2 vLightMapUv;
#endif
#ifdef USE_AOMAP
	uniform mat3 aoMapTransform;
	varying vec2 vAoMapUv;
#endif
#ifdef USE_BUMPMAP
	uniform mat3 bumpMapTransform;
	varying vec2 vBumpMapUv;
#endif
#ifdef USE_NORMALMAP
	uniform mat3 normalMapTransform;
	varying vec2 vNormalMapUv;
#endif
#ifdef USE_DISPLACEMENTMAP
	uniform mat3 displacementMapTransform;
	varying vec2 vDisplacementMapUv;
#endif
#ifdef USE_EMISSIVEMAP
	uniform mat3 emissiveMapTransform;
	varying vec2 vEmissiveMapUv;
#endif
#ifdef USE_METALNESSMAP
	uniform mat3 metalnessMapTransform;
	varying vec2 vMetalnessMapUv;
#endif
#ifdef USE_ROUGHNESSMAP
	uniform mat3 roughnessMapTransform;
	varying vec2 vRoughnessMapUv;
#endif
#ifdef USE_ANISOTROPYMAP
	uniform mat3 anisotropyMapTransform;
	varying vec2 vAnisotropyMapUv;
#endif
#ifdef USE_CLEARCOATMAP
	uniform mat3 clearcoatMapTransform;
	varying vec2 vClearcoatMapUv;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	uniform mat3 clearcoatNormalMapTransform;
	varying vec2 vClearcoatNormalMapUv;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	uniform mat3 clearcoatRoughnessMapTransform;
	varying vec2 vClearcoatRoughnessMapUv;
#endif
#ifdef USE_SHEEN_COLORMAP
	uniform mat3 sheenColorMapTransform;
	varying vec2 vSheenColorMapUv;
#endif
#ifdef USE_SHEEN_ROUGHNESSMAP
	uniform mat3 sheenRoughnessMapTransform;
	varying vec2 vSheenRoughnessMapUv;
#endif
#ifdef USE_IRIDESCENCEMAP
	uniform mat3 iridescenceMapTransform;
	varying vec2 vIridescenceMapUv;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	uniform mat3 iridescenceThicknessMapTransform;
	varying vec2 vIridescenceThicknessMapUv;
#endif
#ifdef USE_SPECULARMAP
	uniform mat3 specularMapTransform;
	varying vec2 vSpecularMapUv;
#endif
#ifdef USE_SPECULAR_COLORMAP
	uniform mat3 specularColorMapTransform;
	varying vec2 vSpecularColorMapUv;
#endif
#ifdef USE_SPECULAR_INTENSITYMAP
	uniform mat3 specularIntensityMapTransform;
	varying vec2 vSpecularIntensityMapUv;
#endif
#ifdef USE_TRANSMISSIONMAP
	uniform mat3 transmissionMapTransform;
	varying vec2 vTransmissionMapUv;
#endif
#ifdef USE_THICKNESSMAP
	uniform mat3 thicknessMapTransform;
	varying vec2 vThicknessMapUv;
#endif`,NU=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
	vUv = vec3( uv, 1 ).xy;
#endif
#ifdef USE_MAP
	vMapUv = ( mapTransform * vec3( MAP_UV, 1 ) ).xy;
#endif
#ifdef USE_ALPHAMAP
	vAlphaMapUv = ( alphaMapTransform * vec3( ALPHAMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_LIGHTMAP
	vLightMapUv = ( lightMapTransform * vec3( LIGHTMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_AOMAP
	vAoMapUv = ( aoMapTransform * vec3( AOMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_BUMPMAP
	vBumpMapUv = ( bumpMapTransform * vec3( BUMPMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_NORMALMAP
	vNormalMapUv = ( normalMapTransform * vec3( NORMALMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_DISPLACEMENTMAP
	vDisplacementMapUv = ( displacementMapTransform * vec3( DISPLACEMENTMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_EMISSIVEMAP
	vEmissiveMapUv = ( emissiveMapTransform * vec3( EMISSIVEMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_METALNESSMAP
	vMetalnessMapUv = ( metalnessMapTransform * vec3( METALNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_ROUGHNESSMAP
	vRoughnessMapUv = ( roughnessMapTransform * vec3( ROUGHNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_ANISOTROPYMAP
	vAnisotropyMapUv = ( anisotropyMapTransform * vec3( ANISOTROPYMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_CLEARCOATMAP
	vClearcoatMapUv = ( clearcoatMapTransform * vec3( CLEARCOATMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	vClearcoatNormalMapUv = ( clearcoatNormalMapTransform * vec3( CLEARCOAT_NORMALMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	vClearcoatRoughnessMapUv = ( clearcoatRoughnessMapTransform * vec3( CLEARCOAT_ROUGHNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_IRIDESCENCEMAP
	vIridescenceMapUv = ( iridescenceMapTransform * vec3( IRIDESCENCEMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	vIridescenceThicknessMapUv = ( iridescenceThicknessMapTransform * vec3( IRIDESCENCE_THICKNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SHEEN_COLORMAP
	vSheenColorMapUv = ( sheenColorMapTransform * vec3( SHEEN_COLORMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SHEEN_ROUGHNESSMAP
	vSheenRoughnessMapUv = ( sheenRoughnessMapTransform * vec3( SHEEN_ROUGHNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SPECULARMAP
	vSpecularMapUv = ( specularMapTransform * vec3( SPECULARMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SPECULAR_COLORMAP
	vSpecularColorMapUv = ( specularColorMapTransform * vec3( SPECULAR_COLORMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SPECULAR_INTENSITYMAP
	vSpecularIntensityMapUv = ( specularIntensityMapTransform * vec3( SPECULAR_INTENSITYMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_TRANSMISSIONMAP
	vTransmissionMapUv = ( transmissionMapTransform * vec3( TRANSMISSIONMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_THICKNESSMAP
	vThicknessMapUv = ( thicknessMapTransform * vec3( THICKNESSMAP_UV, 1 ) ).xy;
#endif`,OU=`#if defined( USE_ENVMAP ) || defined( DISTANCE ) || defined ( USE_SHADOWMAP ) || defined ( USE_TRANSMISSION ) || NUM_SPOT_LIGHT_COORDS > 0
	vec4 worldPosition = vec4( transformed, 1.0 );
	#ifdef USE_BATCHING
		worldPosition = batchingMatrix * worldPosition;
	#endif
	#ifdef USE_INSTANCING
		worldPosition = instanceMatrix * worldPosition;
	#endif
	worldPosition = modelMatrix * worldPosition;
#endif`,FU=`varying vec2 vUv;
uniform mat3 uvTransform;
void main() {
	vUv = ( uvTransform * vec3( uv, 1 ) ).xy;
	gl_Position = vec4( position.xy, 1.0, 1.0 );
}`,RU=`uniform sampler2D t2D;
uniform float backgroundIntensity;
varying vec2 vUv;
void main() {
	vec4 texColor = texture2D( t2D, vUv );
	#ifdef DECODE_VIDEO_TEXTURE
		texColor = vec4( mix( pow( texColor.rgb * 0.9478672986 + vec3( 0.0521327014 ), vec3( 2.4 ) ), texColor.rgb * 0.0773993808, vec3( lessThanEqual( texColor.rgb, vec3( 0.04045 ) ) ) ), texColor.w );
	#endif
	texColor.rgb *= backgroundIntensity;
	gl_FragColor = texColor;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,kU=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
	gl_Position.z = gl_Position.w;
}`,MU=`#ifdef ENVMAP_TYPE_CUBE
	uniform samplerCube envMap;
#elif defined( ENVMAP_TYPE_CUBE_UV )
	uniform sampler2D envMap;
#endif
uniform float flipEnvMap;
uniform float backgroundBlurriness;
uniform float backgroundIntensity;
uniform mat3 backgroundRotation;
varying vec3 vWorldDirection;
#include <cube_uv_reflection_fragment>
void main() {
	#ifdef ENVMAP_TYPE_CUBE
		vec4 texColor = textureCube( envMap, backgroundRotation * vec3( flipEnvMap * vWorldDirection.x, vWorldDirection.yz ) );
	#elif defined( ENVMAP_TYPE_CUBE_UV )
		vec4 texColor = textureCubeUV( envMap, backgroundRotation * vWorldDirection, backgroundBlurriness );
	#else
		vec4 texColor = vec4( 0.0, 0.0, 0.0, 1.0 );
	#endif
	texColor.rgb *= backgroundIntensity;
	gl_FragColor = texColor;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,DU=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
	gl_Position.z = gl_Position.w;
}`,LU=`uniform samplerCube tCube;
uniform float tFlip;
uniform float opacity;
varying vec3 vWorldDirection;
void main() {
	vec4 texColor = textureCube( tCube, vec3( tFlip * vWorldDirection.x, vWorldDirection.yz ) );
	gl_FragColor = texColor;
	gl_FragColor.a *= opacity;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,VU=`#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
varying vec2 vHighPrecisionZW;
void main() {
	#include <uv_vertex>
	#include <batching_vertex>
	#include <skinbase_vertex>
	#include <morphinstance_vertex>
	#ifdef USE_DISPLACEMENTMAP
		#include <beginnormal_vertex>
		#include <morphnormal_vertex>
		#include <skinnormal_vertex>
	#endif
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vHighPrecisionZW = gl_Position.zw;
}`,zU=`#if DEPTH_PACKING == 3200
	uniform float opacity;
#endif
#include <common>
#include <packing>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
varying vec2 vHighPrecisionZW;
void main() {
	vec4 diffuseColor = vec4( 1.0 );
	#include <clipping_planes_fragment>
	#if DEPTH_PACKING == 3200
		diffuseColor.a = opacity;
	#endif
	#include <map_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <logdepthbuf_fragment>
	#ifdef USE_REVERSEDEPTHBUF
		float fragCoordZ = vHighPrecisionZW[ 0 ] / vHighPrecisionZW[ 1 ];
	#else
		float fragCoordZ = 0.5 * vHighPrecisionZW[ 0 ] / vHighPrecisionZW[ 1 ] + 0.5;
	#endif
	#if DEPTH_PACKING == 3200
		gl_FragColor = vec4( vec3( 1.0 - fragCoordZ ), opacity );
	#elif DEPTH_PACKING == 3201
		gl_FragColor = packDepthToRGBA( fragCoordZ );
	#elif DEPTH_PACKING == 3202
		gl_FragColor = vec4( packDepthToRGB( fragCoordZ ), 1.0 );
	#elif DEPTH_PACKING == 3203
		gl_FragColor = vec4( packDepthToRG( fragCoordZ ), 0.0, 1.0 );
	#endif
}`,BU=`#define DISTANCE
varying vec3 vWorldPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <batching_vertex>
	#include <skinbase_vertex>
	#include <morphinstance_vertex>
	#ifdef USE_DISPLACEMENTMAP
		#include <beginnormal_vertex>
		#include <morphnormal_vertex>
		#include <skinnormal_vertex>
	#endif
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <worldpos_vertex>
	#include <clipping_planes_vertex>
	vWorldPosition = worldPosition.xyz;
}`,CU=`#define DISTANCE
uniform vec3 referencePosition;
uniform float nearDistance;
uniform float farDistance;
varying vec3 vWorldPosition;
#include <common>
#include <packing>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <clipping_planes_pars_fragment>
void main () {
	vec4 diffuseColor = vec4( 1.0 );
	#include <clipping_planes_fragment>
	#include <map_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	float dist = length( vWorldPosition - referencePosition );
	dist = ( dist - nearDistance ) / ( farDistance - nearDistance );
	dist = saturate( dist );
	gl_FragColor = packDepthToRGBA( dist );
}`,wU=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
}`,_U=`uniform sampler2D tEquirect;
varying vec3 vWorldDirection;
#include <common>
void main() {
	vec3 direction = normalize( vWorldDirection );
	vec2 sampleUV = equirectUv( direction );
	gl_FragColor = texture2D( tEquirect, sampleUV );
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,IU=`uniform float scale;
attribute float lineDistance;
varying float vLineDistance;
#include <common>
#include <uv_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	vLineDistance = scale * lineDistance;
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <fog_vertex>
}`,PU=`uniform vec3 diffuse;
uniform float opacity;
uniform float dashSize;
uniform float totalSize;
varying float vLineDistance;
#include <common>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <fog_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	if ( mod( vLineDistance, totalSize ) > dashSize ) {
		discard;
	}
	vec3 outgoingLight = vec3( 0.0 );
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	outgoingLight = diffuseColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
}`,TU=`#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <envmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#if defined ( USE_ENVMAP ) || defined ( USE_SKINNING )
		#include <beginnormal_vertex>
		#include <morphnormal_vertex>
		#include <skinbase_vertex>
		#include <skinnormal_vertex>
		#include <defaultnormal_vertex>
	#endif
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <worldpos_vertex>
	#include <envmap_vertex>
	#include <fog_vertex>
}`,AU=`uniform vec3 diffuse;
uniform float opacity;
#ifndef FLAT_SHADED
	varying vec3 vNormal;
#endif
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_pars_fragment>
#include <fog_pars_fragment>
#include <specularmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <specularmap_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	#ifdef USE_LIGHTMAP
		vec4 lightMapTexel = texture2D( lightMap, vLightMapUv );
		reflectedLight.indirectDiffuse += lightMapTexel.rgb * lightMapIntensity * RECIPROCAL_PI;
	#else
		reflectedLight.indirectDiffuse += vec3( 1.0 );
	#endif
	#include <aomap_fragment>
	reflectedLight.indirectDiffuse *= diffuseColor.rgb;
	vec3 outgoingLight = reflectedLight.indirectDiffuse;
	#include <envmap_fragment>
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,SU=`#define LAMBERT
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <envmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <envmap_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,jU=`#define LAMBERT
uniform vec3 diffuse;
uniform vec3 emissive;
uniform float opacity;
#include <common>
#include <packing>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_pars_fragment>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_lambert_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <specularmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <specularmap_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_lambert_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + totalEmissiveRadiance;
	#include <envmap_fragment>
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,yU=`#define MATCAP
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <color_pars_vertex>
#include <displacementmap_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <fog_vertex>
	vViewPosition = - mvPosition.xyz;
}`,vU=`#define MATCAP
uniform vec3 diffuse;
uniform float opacity;
uniform sampler2D matcap;
varying vec3 vViewPosition;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <fog_pars_fragment>
#include <normal_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	vec3 viewDir = normalize( vViewPosition );
	vec3 x = normalize( vec3( viewDir.z, 0.0, - viewDir.x ) );
	vec3 y = cross( viewDir, x );
	vec2 uv = vec2( dot( x, normal ), dot( y, normal ) ) * 0.495 + 0.5;
	#ifdef USE_MATCAP
		vec4 matcapColor = texture2D( matcap, uv );
	#else
		vec4 matcapColor = vec4( vec3( mix( 0.2, 0.8, uv.y ) ), 1.0 );
	#endif
	vec3 outgoingLight = diffuseColor.rgb * matcapColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,fU=`#define NORMAL
#if defined( FLAT_SHADED ) || defined( USE_BUMPMAP ) || defined( USE_NORMALMAP_TANGENTSPACE )
	varying vec3 vViewPosition;
#endif
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphinstance_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
#if defined( FLAT_SHADED ) || defined( USE_BUMPMAP ) || defined( USE_NORMALMAP_TANGENTSPACE )
	vViewPosition = - mvPosition.xyz;
#endif
}`,hU=`#define NORMAL
uniform float opacity;
#if defined( FLAT_SHADED ) || defined( USE_BUMPMAP ) || defined( USE_NORMALMAP_TANGENTSPACE )
	varying vec3 vViewPosition;
#endif
#include <packing>
#include <uv_pars_fragment>
#include <normal_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( 0.0, 0.0, 0.0, opacity );
	#include <clipping_planes_fragment>
	#include <logdepthbuf_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	gl_FragColor = vec4( packNormalToRGB( normal ), diffuseColor.a );
	#ifdef OPAQUE
		gl_FragColor.a = 1.0;
	#endif
}`,bU=`#define PHONG
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <envmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphinstance_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <envmap_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,xU=`#define PHONG
uniform vec3 diffuse;
uniform vec3 emissive;
uniform vec3 specular;
uniform float shininess;
uniform float opacity;
#include <common>
#include <packing>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_pars_fragment>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_phong_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <specularmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <specularmap_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_phong_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + reflectedLight.directSpecular + reflectedLight.indirectSpecular + totalEmissiveRadiance;
	#include <envmap_fragment>
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,gU=`#define STANDARD
varying vec3 vViewPosition;
#ifdef USE_TRANSMISSION
	varying vec3 vWorldPosition;
#endif
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
#ifdef USE_TRANSMISSION
	vWorldPosition = worldPosition.xyz;
#endif
}`,pU=`#define STANDARD
#ifdef PHYSICAL
	#define IOR
	#define USE_SPECULAR
#endif
uniform vec3 diffuse;
uniform vec3 emissive;
uniform float roughness;
uniform float metalness;
uniform float opacity;
#ifdef IOR
	uniform float ior;
#endif
#ifdef USE_SPECULAR
	uniform float specularIntensity;
	uniform vec3 specularColor;
	#ifdef USE_SPECULAR_COLORMAP
		uniform sampler2D specularColorMap;
	#endif
	#ifdef USE_SPECULAR_INTENSITYMAP
		uniform sampler2D specularIntensityMap;
	#endif
#endif
#ifdef USE_CLEARCOAT
	uniform float clearcoat;
	uniform float clearcoatRoughness;
#endif
#ifdef USE_DISPERSION
	uniform float dispersion;
#endif
#ifdef USE_IRIDESCENCE
	uniform float iridescence;
	uniform float iridescenceIOR;
	uniform float iridescenceThicknessMinimum;
	uniform float iridescenceThicknessMaximum;
#endif
#ifdef USE_SHEEN
	uniform vec3 sheenColor;
	uniform float sheenRoughness;
	#ifdef USE_SHEEN_COLORMAP
		uniform sampler2D sheenColorMap;
	#endif
	#ifdef USE_SHEEN_ROUGHNESSMAP
		uniform sampler2D sheenRoughnessMap;
	#endif
#endif
#ifdef USE_ANISOTROPY
	uniform vec2 anisotropyVector;
	#ifdef USE_ANISOTROPYMAP
		uniform sampler2D anisotropyMap;
	#endif
#endif
varying vec3 vViewPosition;
#include <common>
#include <packing>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <iridescence_fragment>
#include <cube_uv_reflection_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_physical_pars_fragment>
#include <fog_pars_fragment>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_physical_pars_fragment>
#include <transmission_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <clearcoat_pars_fragment>
#include <iridescence_pars_fragment>
#include <roughnessmap_pars_fragment>
#include <metalnessmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <roughnessmap_fragment>
	#include <metalnessmap_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <clearcoat_normal_fragment_begin>
	#include <clearcoat_normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_physical_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 totalDiffuse = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse;
	vec3 totalSpecular = reflectedLight.directSpecular + reflectedLight.indirectSpecular;
	#include <transmission_fragment>
	vec3 outgoingLight = totalDiffuse + totalSpecular + totalEmissiveRadiance;
	#ifdef USE_SHEEN
		float sheenEnergyComp = 1.0 - 0.157 * max3( material.sheenColor );
		outgoingLight = outgoingLight * sheenEnergyComp + sheenSpecularDirect + sheenSpecularIndirect;
	#endif
	#ifdef USE_CLEARCOAT
		float dotNVcc = saturate( dot( geometryClearcoatNormal, geometryViewDir ) );
		vec3 Fcc = F_Schlick( material.clearcoatF0, material.clearcoatF90, dotNVcc );
		outgoingLight = outgoingLight * ( 1.0 - material.clearcoat * Fcc ) + ( clearcoatSpecularDirect + clearcoatSpecularIndirect ) * material.clearcoat;
	#endif
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,lU=`#define TOON
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,dU=`#define TOON
uniform vec3 diffuse;
uniform vec3 emissive;
uniform float opacity;
#include <common>
#include <packing>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <gradientmap_pars_fragment>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_toon_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_toon_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + totalEmissiveRadiance;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,mU=`uniform float size;
uniform float scale;
#include <common>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
#ifdef USE_POINTS_UV
	varying vec2 vUv;
	uniform mat3 uvTransform;
#endif
void main() {
	#ifdef USE_POINTS_UV
		vUv = ( uvTransform * vec3( uv, 1 ) ).xy;
	#endif
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <project_vertex>
	gl_PointSize = size;
	#ifdef USE_SIZEATTENUATION
		bool isPerspective = isPerspectiveMatrix( projectionMatrix );
		if ( isPerspective ) gl_PointSize *= ( scale / - mvPosition.z );
	#endif
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <worldpos_vertex>
	#include <fog_vertex>
}`,uU=`uniform vec3 diffuse;
uniform float opacity;
#include <common>
#include <color_pars_fragment>
#include <map_particle_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <fog_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	vec3 outgoingLight = vec3( 0.0 );
	#include <logdepthbuf_fragment>
	#include <map_particle_fragment>
	#include <color_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	outgoingLight = diffuseColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
}`,cU=`#include <common>
#include <batching_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <shadowmap_pars_vertex>
void main() {
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphinstance_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <worldpos_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,nU=`uniform vec3 color;
uniform float opacity;
#include <common>
#include <packing>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <logdepthbuf_pars_fragment>
#include <shadowmap_pars_fragment>
#include <shadowmask_pars_fragment>
void main() {
	#include <logdepthbuf_fragment>
	gl_FragColor = vec4( color, opacity * ( 1.0 - getShadowMask() ) );
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
}`,sU=`uniform float rotation;
uniform vec2 center;
#include <common>
#include <uv_pars_vertex>
#include <fog_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	vec4 mvPosition = modelViewMatrix[ 3 ];
	vec2 scale = vec2( length( modelMatrix[ 0 ].xyz ), length( modelMatrix[ 1 ].xyz ) );
	#ifndef USE_SIZEATTENUATION
		bool isPerspective = isPerspectiveMatrix( projectionMatrix );
		if ( isPerspective ) scale *= - mvPosition.z;
	#endif
	vec2 alignedPosition = ( position.xy - ( center - vec2( 0.5 ) ) ) * scale;
	vec2 rotatedPosition;
	rotatedPosition.x = cos( rotation ) * alignedPosition.x - sin( rotation ) * alignedPosition.y;
	rotatedPosition.y = sin( rotation ) * alignedPosition.x + cos( rotation ) * alignedPosition.y;
	mvPosition.xy += rotatedPosition;
	gl_Position = projectionMatrix * mvPosition;
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <fog_vertex>
}`,oU=`uniform vec3 diffuse;
uniform float opacity;
#include <common>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <fog_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	vec3 outgoingLight = vec3( 0.0 );
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	outgoingLight = diffuseColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
}`,hJ={alphahash_fragment:RX,alphahash_pars_fragment:kX,alphamap_fragment:MX,alphamap_pars_fragment:DX,alphatest_fragment:LX,alphatest_pars_fragment:VX,aomap_fragment:zX,aomap_pars_fragment:BX,batching_pars_vertex:CX,batching_vertex:wX,begin_vertex:_X,beginnormal_vertex:IX,bsdfs:PX,iridescence_fragment:TX,bumpmap_pars_fragment:AX,clipping_planes_fragment:SX,clipping_planes_pars_fragment:jX,clipping_planes_pars_vertex:yX,clipping_planes_vertex:vX,color_fragment:fX,color_pars_fragment:hX,color_pars_vertex:bX,color_vertex:xX,common:gX,cube_uv_reflection_fragment:pX,defaultnormal_vertex:lX,displacementmap_pars_vertex:dX,displacementmap_vertex:mX,emissivemap_fragment:uX,emissivemap_pars_fragment:cX,colorspace_fragment:nX,colorspace_pars_fragment:sX,envmap_fragment:oX,envmap_common_pars_fragment:iX,envmap_pars_fragment:aX,envmap_pars_vertex:rX,envmap_physical_pars_fragment:KK,envmap_vertex:tX,fog_vertex:eX,fog_pars_vertex:JK,fog_fragment:QK,fog_pars_fragment:$K,gradientmap_pars_fragment:ZK,lightmap_pars_fragment:WK,lights_lambert_fragment:HK,lights_lambert_pars_fragment:YK,lights_pars_begin:XK,lights_toon_fragment:UK,lights_toon_pars_fragment:GK,lights_phong_fragment:qK,lights_phong_pars_fragment:EK,lights_physical_fragment:NK,lights_physical_pars_fragment:OK,lights_fragment_begin:FK,lights_fragment_maps:RK,lights_fragment_end:kK,logdepthbuf_fragment:MK,logdepthbuf_pars_fragment:DK,logdepthbuf_pars_vertex:LK,logdepthbuf_vertex:VK,map_fragment:zK,map_pars_fragment:BK,map_particle_fragment:CK,map_particle_pars_fragment:wK,metalnessmap_fragment:_K,metalnessmap_pars_fragment:IK,morphinstance_vertex:PK,morphcolor_vertex:TK,morphnormal_vertex:AK,morphtarget_pars_vertex:SK,morphtarget_vertex:jK,normal_fragment_begin:yK,normal_fragment_maps:vK,normal_pars_fragment:fK,normal_pars_vertex:hK,normal_vertex:bK,normalmap_pars_fragment:xK,clearcoat_normal_fragment_begin:gK,clearcoat_normal_fragment_maps:pK,clearcoat_pars_fragment:lK,iridescence_pars_fragment:dK,opaque_fragment:mK,packing:uK,premultiplied_alpha_fragment:cK,project_vertex:nK,dithering_fragment:sK,dithering_pars_fragment:oK,roughnessmap_fragment:iK,roughnessmap_pars_fragment:aK,shadowmap_pars_fragment:rK,shadowmap_pars_vertex:tK,shadowmap_vertex:eK,shadowmask_pars_fragment:JU,skinbase_vertex:QU,skinning_pars_vertex:$U,skinning_vertex:ZU,skinnormal_vertex:WU,specularmap_fragment:HU,specularmap_pars_fragment:YU,tonemapping_fragment:XU,tonemapping_pars_fragment:KU,transmission_fragment:UU,transmission_pars_fragment:GU,uv_pars_fragment:qU,uv_pars_vertex:EU,uv_vertex:NU,worldpos_vertex:OU,background_vert:FU,background_frag:RU,backgroundCube_vert:kU,backgroundCube_frag:MU,cube_vert:DU,cube_frag:LU,depth_vert:VU,depth_frag:zU,distanceRGBA_vert:BU,distanceRGBA_frag:CU,equirect_vert:wU,equirect_frag:_U,linedashed_vert:IU,linedashed_frag:PU,meshbasic_vert:TU,meshbasic_frag:AU,meshlambert_vert:SU,meshlambert_frag:jU,meshmatcap_vert:yU,meshmatcap_frag:vU,meshnormal_vert:fU,meshnormal_frag:hU,meshphong_vert:bU,meshphong_frag:xU,meshphysical_vert:gU,meshphysical_frag:pU,meshtoon_vert:lU,meshtoon_frag:dU,points_vert:mU,points_frag:uU,shadow_vert:cU,shadow_frag:nU,sprite_vert:sU,sprite_frag:oU},$J={common:{diffuse:{value:new jJ(16777215)},opacity:{value:1},map:{value:null},mapTransform:{value:new fJ},alphaMap:{value:null},alphaMapTransform:{value:new fJ},alphaTest:{value:0}},specularmap:{specularMap:{value:null},specularMapTransform:{value:new fJ}},envmap:{envMap:{value:null},envMapRotation:{value:new fJ},flipEnvMap:{value:-1},reflectivity:{value:1},ior:{value:1.5},refractionRatio:{value:0.98}},aomap:{aoMap:{value:null},aoMapIntensity:{value:1},aoMapTransform:{value:new fJ}},lightmap:{lightMap:{value:null},lightMapIntensity:{value:1},lightMapTransform:{value:new fJ}},bumpmap:{bumpMap:{value:null},bumpMapTransform:{value:new fJ},bumpScale:{value:1}},normalmap:{normalMap:{value:null},normalMapTransform:{value:new fJ},normalScale:{value:new PJ(1,1)}},displacementmap:{displacementMap:{value:null},displacementMapTransform:{value:new fJ},displacementScale:{value:1},displacementBias:{value:0}},emissivemap:{emissiveMap:{value:null},emissiveMapTransform:{value:new fJ}},metalnessmap:{metalnessMap:{value:null},metalnessMapTransform:{value:new fJ}},roughnessmap:{roughnessMap:{value:null},roughnessMapTransform:{value:new fJ}},gradientmap:{gradientMap:{value:null}},fog:{fogDensity:{value:0.00025},fogNear:{value:1},fogFar:{value:2000},fogColor:{value:new jJ(16777215)}},lights:{ambientLightColor:{value:[]},lightProbe:{value:[]},directionalLights:{value:[],properties:{direction:{},color:{}}},directionalLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},directionalShadowMap:{value:[]},directionalShadowMatrix:{value:[]},spotLights:{value:[],properties:{color:{},position:{},direction:{},distance:{},coneCos:{},penumbraCos:{},decay:{}}},spotLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},spotLightMap:{value:[]},spotShadowMap:{value:[]},spotLightMatrix:{value:[]},pointLights:{value:[],properties:{color:{},position:{},decay:{},distance:{}}},pointLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{},shadowCameraNear:{},shadowCameraFar:{}}},pointShadowMap:{value:[]},pointShadowMatrix:{value:[]},hemisphereLights:{value:[],properties:{direction:{},skyColor:{},groundColor:{}}},rectAreaLights:{value:[],properties:{color:{},position:{},width:{},height:{}}},ltc_1:{value:null},ltc_2:{value:null}},points:{diffuse:{value:new jJ(16777215)},opacity:{value:1},size:{value:1},scale:{value:1},map:{value:null},alphaMap:{value:null},alphaMapTransform:{value:new fJ},alphaTest:{value:0},uvTransform:{value:new fJ}},sprite:{diffuse:{value:new jJ(16777215)},opacity:{value:1},center:{value:new PJ(0.5,0.5)},rotation:{value:0},map:{value:null},mapTransform:{value:new fJ},alphaMap:{value:null},alphaMapTransform:{value:new fJ},alphaTest:{value:0}}},E8={basic:{uniforms:w0([$J.common,$J.specularmap,$J.envmap,$J.aomap,$J.lightmap,$J.fog]),vertexShader:hJ.meshbasic_vert,fragmentShader:hJ.meshbasic_frag},lambert:{uniforms:w0([$J.common,$J.specularmap,$J.envmap,$J.aomap,$J.lightmap,$J.emissivemap,$J.bumpmap,$J.normalmap,$J.displacementmap,$J.fog,$J.lights,{emissive:{value:new jJ(0)}}]),vertexShader:hJ.meshlambert_vert,fragmentShader:hJ.meshlambert_frag},phong:{uniforms:w0([$J.common,$J.specularmap,$J.envmap,$J.aomap,$J.lightmap,$J.emissivemap,$J.bumpmap,$J.normalmap,$J.displacementmap,$J.fog,$J.lights,{emissive:{value:new jJ(0)},specular:{value:new jJ(1118481)},shininess:{value:30}}]),vertexShader:hJ.meshphong_vert,fragmentShader:hJ.meshphong_frag},standard:{uniforms:w0([$J.common,$J.envmap,$J.aomap,$J.lightmap,$J.emissivemap,$J.bumpmap,$J.normalmap,$J.displacementmap,$J.roughnessmap,$J.metalnessmap,$J.fog,$J.lights,{emissive:{value:new jJ(0)},roughness:{value:1},metalness:{value:0},envMapIntensity:{value:1}}]),vertexShader:hJ.meshphysical_vert,fragmentShader:hJ.meshphysical_frag},toon:{uniforms:w0([$J.common,$J.aomap,$J.lightmap,$J.emissivemap,$J.bumpmap,$J.normalmap,$J.displacementmap,$J.gradientmap,$J.fog,$J.lights,{emissive:{value:new jJ(0)}}]),vertexShader:hJ.meshtoon_vert,fragmentShader:hJ.meshtoon_frag},matcap:{uniforms:w0([$J.common,$J.bumpmap,$J.normalmap,$J.displacementmap,$J.fog,{matcap:{value:null}}]),vertexShader:hJ.meshmatcap_vert,fragmentShader:hJ.meshmatcap_frag},points:{uniforms:w0([$J.points,$J.fog]),vertexShader:hJ.points_vert,fragmentShader:hJ.points_frag},dashed:{uniforms:w0([$J.common,$J.fog,{scale:{value:1},dashSize:{value:1},totalSize:{value:2}}]),vertexShader:hJ.linedashed_vert,fragmentShader:hJ.linedashed_frag},depth:{uniforms:w0([$J.common,$J.displacementmap]),vertexShader:hJ.depth_vert,fragmentShader:hJ.depth_frag},normal:{uniforms:w0([$J.common,$J.bumpmap,$J.normalmap,$J.displacementmap,{opacity:{value:1}}]),vertexShader:hJ.meshnormal_vert,fragmentShader:hJ.meshnormal_frag},sprite:{uniforms:w0([$J.sprite,$J.fog]),vertexShader:hJ.sprite_vert,fragmentShader:hJ.sprite_frag},background:{uniforms:{uvTransform:{value:new fJ},t2D:{value:null},backgroundIntensity:{value:1}},vertexShader:hJ.background_vert,fragmentShader:hJ.background_frag},backgroundCube:{uniforms:{envMap:{value:null},flipEnvMap:{value:-1},backgroundBlurriness:{value:0},backgroundIntensity:{value:1},backgroundRotation:{value:new fJ}},vertexShader:hJ.backgroundCube_vert,fragmentShader:hJ.backgroundCube_frag},cube:{uniforms:{tCube:{value:null},tFlip:{value:-1},opacity:{value:1}},vertexShader:hJ.cube_vert,fragmentShader:hJ.cube_frag},equirect:{uniforms:{tEquirect:{value:null}},vertexShader:hJ.equirect_vert,fragmentShader:hJ.equirect_frag},distanceRGBA:{uniforms:w0([$J.common,$J.displacementmap,{referencePosition:{value:new A},nearDistance:{value:1},farDistance:{value:1000}}]),vertexShader:hJ.distanceRGBA_vert,fragmentShader:hJ.distanceRGBA_frag},shadow:{uniforms:w0([$J.lights,$J.fog,{color:{value:new jJ(0)},opacity:{value:1}}]),vertexShader:hJ.shadow_vert,fragmentShader:hJ.shadow_frag}};E8.physical={uniforms:w0([E8.standard.uniforms,{clearcoat:{value:0},clearcoatMap:{value:null},clearcoatMapTransform:{value:new fJ},clearcoatNormalMap:{value:null},clearcoatNormalMapTransform:{value:new fJ},clearcoatNormalScale:{value:new PJ(1,1)},clearcoatRoughness:{value:0},clearcoatRoughnessMap:{value:null},clearcoatRoughnessMapTransform:{value:new fJ},dispersion:{value:0},iridescence:{value:0},iridescenceMap:{value:null},iridescenceMapTransform:{value:new fJ},iridescenceIOR:{value:1.3},iridescenceThicknessMinimum:{value:100},iridescenceThicknessMaximum:{value:400},iridescenceThicknessMap:{value:null},iridescenceThicknessMapTransform:{value:new fJ},sheen:{value:0},sheenColor:{value:new jJ(0)},sheenColorMap:{value:null},sheenColorMapTransform:{value:new fJ},sheenRoughness:{value:1},sheenRoughnessMap:{value:null},sheenRoughnessMapTransform:{value:new fJ},transmission:{value:0},transmissionMap:{value:null},transmissionMapTransform:{value:new fJ},transmissionSamplerSize:{value:new PJ},transmissionSamplerMap:{value:null},thickness:{value:0},thicknessMap:{value:null},thicknessMapTransform:{value:new fJ},attenuationDistance:{value:0},attenuationColor:{value:new jJ(0)},specularColor:{value:new jJ(1,1,1)},specularColorMap:{value:null},specularColorMapTransform:{value:new fJ},specularIntensity:{value:1},specularIntensityMap:{value:null},specularIntensityMapTransform:{value:new fJ},anisotropyVector:{value:new PJ},anisotropyMap:{value:null},anisotropyMapTransform:{value:new fJ}}]),vertexShader:hJ.meshphysical_vert,fragmentShader:hJ.meshphysical_frag};var m7={r:0,b:0,g:0},U9=new $8,iU=new vJ;function aU(J,Q,$,Z,W,H,Y){let X=new jJ(0),K=H===!0?0:1,U,G,q=null,E=0,F=null;function k(L){let w=L.isScene===!0?L.background:null;if(w&&w.isTexture)w=(L.backgroundBlurriness>0?$:Q).get(w);return w}function M(L){let w=!1,v=k(L);if(v===null)O(X,K);else if(v&&v.isColor)O(v,1),w=!0;let _=J.xr.getEnvironmentBlendMode();if(_==="additive")Z.buffers.color.setClear(0,0,0,1,Y);else if(_==="alpha-blend")Z.buffers.color.setClear(0,0,0,0,Y);if(J.autoClear||w)Z.buffers.depth.setTest(!0),Z.buffers.depth.setMask(!0),Z.buffers.color.setMask(!0),J.clear(J.autoClearColor,J.autoClearDepth,J.autoClearStencil)}function N(L,w){let v=k(w);if(v&&(v.isCubeTexture||v.mapping===K6)){if(G===void 0)G=new C0(new x9(1,1,1),new q8({name:"BackgroundCubeMaterial",uniforms:K9(E8.backgroundCube.uniforms),vertexShader:E8.backgroundCube.vertexShader,fragmentShader:E8.backgroundCube.fragmentShader,side:b0,depthTest:!1,depthWrite:!1,fog:!1,allowOverride:!1})),G.geometry.deleteAttribute("normal"),G.geometry.deleteAttribute("uv"),G.onBeforeRender=function(_,T,x){this.matrixWorld.copyPosition(x.matrixWorld)},Object.defineProperty(G.material,"envMap",{get:function(){return this.uniforms.envMap.value}}),W.update(G);if(U9.copy(w.backgroundRotation),U9.x*=-1,U9.y*=-1,U9.z*=-1,v.isCubeTexture&&v.isRenderTargetTexture===!1)U9.y*=-1,U9.z*=-1;if(G.material.uniforms.envMap.value=v,G.material.uniforms.flipEnvMap.value=v.isCubeTexture&&v.isRenderTargetTexture===!1?-1:1,G.material.uniforms.backgroundBlurriness.value=w.backgroundBlurriness,G.material.uniforms.backgroundIntensity.value=w.backgroundIntensity,G.material.uniforms.backgroundRotation.value.setFromMatrix4(iU.makeRotationFromEuler(U9)),G.material.toneMapped=lJ.getTransfer(v.colorSpace)!==W0,q!==v||E!==v.version||F!==J.toneMapping)G.material.needsUpdate=!0,q=v,E=v.version,F=J.toneMapping;G.layers.enableAll(),L.unshift(G,G.geometry,G.material,0,0,null)}else if(v&&v.isTexture){if(U===void 0)U=new C0(new V6(2,2),new q8({name:"BackgroundMaterial",uniforms:K9(E8.background.uniforms),vertexShader:E8.background.vertexShader,fragmentShader:E8.background.fragmentShader,side:x8,depthTest:!1,depthWrite:!1,fog:!1,allowOverride:!1})),U.geometry.deleteAttribute("normal"),Object.defineProperty(U.material,"map",{get:function(){return this.uniforms.t2D.value}}),W.update(U);if(U.material.uniforms.t2D.value=v,U.material.uniforms.backgroundIntensity.value=w.backgroundIntensity,U.material.toneMapped=lJ.getTransfer(v.colorSpace)!==W0,v.matrixAutoUpdate===!0)v.updateMatrix();if(U.material.uniforms.uvTransform.value.copy(v.matrix),q!==v||E!==v.version||F!==J.toneMapping)U.material.needsUpdate=!0,q=v,E=v.version,F=J.toneMapping;U.layers.enableAll(),L.unshift(U,U.geometry,U.material,0,0,null)}}function O(L,w){L.getRGB(m7,M$(J)),Z.buffers.color.setClear(m7.r,m7.g,m7.b,w,Y)}function C(){if(G!==void 0)G.geometry.dispose(),G.material.dispose(),G=void 0;if(U!==void 0)U.geometry.dispose(),U.material.dispose(),U=void 0}return{getClearColor:function(){return X},setClearColor:function(L,w=1){X.set(L),K=w,O(X,K)},getClearAlpha:function(){return K},setClearAlpha:function(L){K=L,O(X,K)},render:M,addToRenderList:N,dispose:C}}function rU(J,Q){let $=J.getParameter(J.MAX_VERTEX_ATTRIBS),Z={},W=E(null),H=W,Y=!1;function X(V,j,m,l,c){let i=!1,u=q(l,m,j);if(H!==u)H=u,U(H.object);if(i=F(V,l,m,c),i)k(V,l,m,c);if(c!==null)Q.update(c,J.ELEMENT_ARRAY_BUFFER);if(i||Y){if(Y=!1,w(V,j,m,l),c!==null)J.bindBuffer(J.ELEMENT_ARRAY_BUFFER,Q.get(c).buffer)}}function K(){return J.createVertexArray()}function U(V){return J.bindVertexArray(V)}function G(V){return J.deleteVertexArray(V)}function q(V,j,m){let l=m.wireframe===!0,c=Z[V.id];if(c===void 0)c={},Z[V.id]=c;let i=c[j.id];if(i===void 0)i={},c[j.id]=i;let u=i[l];if(u===void 0)u=E(K()),i[l]=u;return u}function E(V){let j=[],m=[],l=[];for(let c=0;c<$;c++)j[c]=0,m[c]=0,l[c]=0;return{geometry:null,program:null,wireframe:!1,newAttributes:j,enabledAttributes:m,attributeDivisors:l,object:V,attributes:{},index:null}}function F(V,j,m,l){let c=H.attributes,i=j.attributes,u=0,r=m.getAttributes();for(let g in r)if(r[g].location>=0){let UJ=c[g],TJ=i[g];if(TJ===void 0){if(g==="instanceMatrix"&&V.instanceMatrix)TJ=V.instanceMatrix;if(g==="instanceColor"&&V.instanceColor)TJ=V.instanceColor}if(UJ===void 0)return!0;if(UJ.attribute!==TJ)return!0;if(TJ&&UJ.data!==TJ.data)return!0;u++}if(H.attributesNum!==u)return!0;if(H.index!==l)return!0;return!1}function k(V,j,m,l){let c={},i=j.attributes,u=0,r=m.getAttributes();for(let g in r)if(r[g].location>=0){let UJ=i[g];if(UJ===void 0){if(g==="instanceMatrix"&&V.instanceMatrix)UJ=V.instanceMatrix;if(g==="instanceColor"&&V.instanceColor)UJ=V.instanceColor}let TJ={};if(TJ.attribute=UJ,UJ&&UJ.data)TJ.data=UJ.data;c[g]=TJ,u++}H.attributes=c,H.attributesNum=u,H.index=l}function M(){let V=H.newAttributes;for(let j=0,m=V.length;j<m;j++)V[j]=0}function N(V){O(V,0)}function O(V,j){let{newAttributes:m,enabledAttributes:l,attributeDivisors:c}=H;if(m[V]=1,l[V]===0)J.enableVertexAttribArray(V),l[V]=1;if(c[V]!==j)J.vertexAttribDivisor(V,j),c[V]=j}function C(){let{newAttributes:V,enabledAttributes:j}=H;for(let m=0,l=j.length;m<l;m++)if(j[m]!==V[m])J.disableVertexAttribArray(m),j[m]=0}function L(V,j,m,l,c,i,u){if(u===!0)J.vertexAttribIPointer(V,j,m,c,i);else J.vertexAttribPointer(V,j,m,l,c,i)}function w(V,j,m,l){M();let c=l.attributes,i=m.getAttributes(),u=j.defaultAttributeValues;for(let r in i){let g=i[r];if(g.location>=0){let ZJ=c[r];if(ZJ===void 0){if(r==="instanceMatrix"&&V.instanceMatrix)ZJ=V.instanceMatrix;if(r==="instanceColor"&&V.instanceColor)ZJ=V.instanceColor}if(ZJ!==void 0){let{normalized:UJ,itemSize:TJ}=ZJ,mJ=Q.get(ZJ);if(mJ===void 0)continue;let{buffer:Y0,type:d,bytesPerElement:WJ}=mJ,MJ=d===J.INT||d===J.UNSIGNED_INT||ZJ.gpuType===TQ;if(ZJ.isInterleavedBufferAttribute){let GJ=ZJ.data,RJ=GJ.stride,uJ=ZJ.offset;if(GJ.isInstancedInterleavedBuffer){for(let cJ=0;cJ<g.locationSize;cJ++)O(g.location+cJ,GJ.meshPerAttribute);if(V.isInstancedMesh!==!0&&l._maxInstanceCount===void 0)l._maxInstanceCount=GJ.meshPerAttribute*GJ.count}else for(let cJ=0;cJ<g.locationSize;cJ++)N(g.location+cJ);J.bindBuffer(J.ARRAY_BUFFER,Y0);for(let cJ=0;cJ<g.locationSize;cJ++)L(g.location+cJ,TJ/g.locationSize,d,UJ,RJ*WJ,(uJ+TJ/g.locationSize*cJ)*WJ,MJ)}else{if(ZJ.isInstancedBufferAttribute){for(let GJ=0;GJ<g.locationSize;GJ++)O(g.location+GJ,ZJ.meshPerAttribute);if(V.isInstancedMesh!==!0&&l._maxInstanceCount===void 0)l._maxInstanceCount=ZJ.meshPerAttribute*ZJ.count}else for(let GJ=0;GJ<g.locationSize;GJ++)N(g.location+GJ);J.bindBuffer(J.ARRAY_BUFFER,Y0);for(let GJ=0;GJ<g.locationSize;GJ++)L(g.location+GJ,TJ/g.locationSize,d,UJ,TJ*WJ,TJ/g.locationSize*GJ*WJ,MJ)}}else if(u!==void 0){let UJ=u[r];if(UJ!==void 0)switch(UJ.length){case 2:J.vertexAttrib2fv(g.location,UJ);break;case 3:J.vertexAttrib3fv(g.location,UJ);break;case 4:J.vertexAttrib4fv(g.location,UJ);break;default:J.vertexAttrib1fv(g.location,UJ)}}}}C()}function v(){x();for(let V in Z){let j=Z[V];for(let m in j){let l=j[m];for(let c in l)G(l[c].object),delete l[c];delete j[m]}delete Z[V]}}function _(V){if(Z[V.id]===void 0)return;let j=Z[V.id];for(let m in j){let l=j[m];for(let c in l)G(l[c].object),delete l[c];delete j[m]}delete Z[V.id]}function T(V){for(let j in Z){let m=Z[j];if(m[V.id]===void 0)continue;let l=m[V.id];for(let c in l)G(l[c].object),delete l[c];delete m[V.id]}}function x(){if(z(),Y=!0,H===W)return;H=W,U(H.object)}function z(){W.geometry=null,W.program=null,W.wireframe=!1}return{setup:X,reset:x,resetDefaultState:z,dispose:v,releaseStatesOfGeometry:_,releaseStatesOfProgram:T,initAttributes:M,enableAttribute:N,disableUnusedAttributes:C}}function tU(J,Q,$){let Z;function W(U){Z=U}function H(U,G){J.drawArrays(Z,U,G),$.update(G,Z,1)}function Y(U,G,q){if(q===0)return;J.drawArraysInstanced(Z,U,G,q),$.update(G,Z,q)}function X(U,G,q){if(q===0)return;Q.get("WEBGL_multi_draw").multiDrawArraysWEBGL(Z,U,0,G,0,q);let F=0;for(let k=0;k<q;k++)F+=G[k];$.update(F,Z,1)}function K(U,G,q,E){if(q===0)return;let F=Q.get("WEBGL_multi_draw");if(F===null)for(let k=0;k<U.length;k++)Y(U[k],G[k],E[k]);else{F.multiDrawArraysInstancedWEBGL(Z,U,0,G,0,E,0,q);let k=0;for(let M=0;M<q;M++)k+=G[M]*E[M];$.update(k,Z,1)}}this.setMode=W,this.render=H,this.renderInstances=Y,this.renderMultiDraw=X,this.renderMultiDrawInstances=K}function eU(J,Q,$,Z){let W;function H(){if(W!==void 0)return W;if(Q.has("EXT_texture_filter_anisotropic")===!0){let T=Q.get("EXT_texture_filter_anisotropic");W=J.getParameter(T.MAX_TEXTURE_MAX_ANISOTROPY_EXT)}else W=0;return W}function Y(T){if(T!==U8&&Z.convert(T)!==J.getParameter(J.IMPLEMENTATION_COLOR_READ_FORMAT))return!1;return!0}function X(T){let x=T===G6&&(Q.has("EXT_color_buffer_half_float")||Q.has("EXT_color_buffer_float"));if(T!==p8&&Z.convert(T)!==J.getParameter(J.IMPLEMENTATION_COLOR_READ_TYPE)&&T!==l8&&!x)return!1;return!0}function K(T){if(T==="highp"){if(J.getShaderPrecisionFormat(J.VERTEX_SHADER,J.HIGH_FLOAT).precision>0&&J.getShaderPrecisionFormat(J.FRAGMENT_SHADER,J.HIGH_FLOAT).precision>0)return"highp";T="mediump"}if(T==="mediump"){if(J.getShaderPrecisionFormat(J.VERTEX_SHADER,J.MEDIUM_FLOAT).precision>0&&J.getShaderPrecisionFormat(J.FRAGMENT_SHADER,J.MEDIUM_FLOAT).precision>0)return"mediump"}return"lowp"}let U=$.precision!==void 0?$.precision:"highp",G=K(U);if(G!==U)console.warn("THREE.WebGLRenderer:",U,"not supported, using",G,"instead."),U=G;let q=$.logarithmicDepthBuffer===!0,E=$.reversedDepthBuffer===!0&&Q.has("EXT_clip_control"),F=J.getParameter(J.MAX_TEXTURE_IMAGE_UNITS),k=J.getParameter(J.MAX_VERTEX_TEXTURE_IMAGE_UNITS),M=J.getParameter(J.MAX_TEXTURE_SIZE),N=J.getParameter(J.MAX_CUBE_MAP_TEXTURE_SIZE),O=J.getParameter(J.MAX_VERTEX_ATTRIBS),C=J.getParameter(J.MAX_VERTEX_UNIFORM_VECTORS),L=J.getParameter(J.MAX_VARYING_VECTORS),w=J.getParameter(J.MAX_FRAGMENT_UNIFORM_VECTORS),v=k>0,_=J.getParameter(J.MAX_SAMPLES);return{isWebGL2:!0,getMaxAnisotropy:H,getMaxPrecision:K,textureFormatReadable:Y,textureTypeReadable:X,precision:U,logarithmicDepthBuffer:q,reversedDepthBuffer:E,maxTextures:F,maxVertexTextures:k,maxTextureSize:M,maxCubemapSize:N,maxAttributes:O,maxVertexUniforms:C,maxVaryings:L,maxFragmentUniforms:w,vertexTextures:v,maxSamples:_}}function JG(J){let Q=this,$=null,Z=0,W=!1,H=!1,Y=new e0,X=new fJ,K={value:null,needsUpdate:!1};this.uniform=K,this.numPlanes=0,this.numIntersection=0,this.init=function(q,E){let F=q.length!==0||E||Z!==0||W;return W=E,Z=q.length,F},this.beginShadows=function(){H=!0,G(null)},this.endShadows=function(){H=!1},this.setGlobalState=function(q,E){$=G(q,E,0)},this.setState=function(q,E,F){let{clippingPlanes:k,clipIntersection:M,clipShadows:N}=q,O=J.get(q);if(!W||k===null||k.length===0||H&&!N)if(H)G(null);else U();else{let C=H?0:Z,L=C*4,w=O.clippingState||null;K.value=w,w=G(k,E,L,F);for(let v=0;v!==L;++v)w[v]=$[v];O.clippingState=w,this.numIntersection=M?this.numPlanes:0,this.numPlanes+=C}};function U(){if(K.value!==$)K.value=$,K.needsUpdate=Z>0;Q.numPlanes=Z,Q.numIntersection=0}function G(q,E,F,k){let M=q!==null?q.length:0,N=null;if(M!==0){if(N=K.value,k!==!0||N===null){let O=F+M*4,C=E.matrixWorldInverse;if(X.getNormalMatrix(C),N===null||N.length<O)N=new Float32Array(O);for(let L=0,w=F;L!==M;++L,w+=4)Y.copy(q[L]).applyMatrix4(C,X),Y.normal.toArray(N,w),N[w+3]=Y.constant}K.value=N,K.needsUpdate=!0}return Q.numPlanes=M,Q.numIntersection=0,N}}function QG(J){let Q=new WeakMap;function $(Y,X){if(X===K7)Y.mapping=j9;else if(X===U7)Y.mapping=W9;return Y}function Z(Y){if(Y&&Y.isTexture){let X=Y.mapping;if(X===K7||X===U7)if(Q.has(Y)){let K=Q.get(Y).texture;return $(K,Y.mapping)}else{let K=Y.image;if(K&&K.height>0){let U=new L$(K.height);return U.fromEquirectangularTexture(J,Y),Q.set(Y,U),Y.addEventListener("dispose",W),$(U.texture,Y.mapping)}else return null}}return Y}function W(Y){let X=Y.target;X.removeEventListener("dispose",W);let K=Q.get(X);if(K!==void 0)Q.delete(X),K.dispose()}function H(){Q=new WeakMap}return{get:Z,dispose:H}}var n9=4,rW=[0.125,0.215,0.35,0.446,0.526,0.582],E9=20,y$=new m9,tW=new jJ,v$=null,f$=0,h$=0,b$=!1,q9=(1+Math.sqrt(5))/2,c9=1/q9,eW=[new A(-q9,c9,0),new A(q9,c9,0),new A(-c9,0,q9),new A(c9,0,q9),new A(0,q9,-c9),new A(0,q9,c9),new A(-1,1,-1),new A(1,1,-1),new A(-1,1,1),new A(1,1,1)],$G=new A;class g${constructor(J){this._renderer=J,this._pingPongRenderTarget=null,this._lodMax=0,this._cubeSize=0,this._lodPlanes=[],this._sizeLods=[],this._sigmas=[],this._blurMaterial=null,this._cubemapMaterial=null,this._equirectMaterial=null,this._compileMaterial(this._blurMaterial)}fromScene(J,Q=0,$=0.1,Z=100,W={}){let{size:H=256,position:Y=$G}=W;v$=this._renderer.getRenderTarget(),f$=this._renderer.getActiveCubeFace(),h$=this._renderer.getActiveMipmapLevel(),b$=this._renderer.xr.enabled,this._renderer.xr.enabled=!1,this._setSize(H);let X=this._allocateTargets();if(X.depthBuffer=!0,this._sceneToCubeUV(J,$,Z,X,Y),Q>0)this._blur(X,0,0,Q);return this._applyPMREM(X),this._cleanup(X),X}fromEquirectangular(J,Q=null){return this._fromTexture(J,Q)}fromCubemap(J,Q=null){return this._fromTexture(J,Q)}compileCubemapShader(){if(this._cubemapMaterial===null)this._cubemapMaterial=$H(),this._compileMaterial(this._cubemapMaterial)}compileEquirectangularShader(){if(this._equirectMaterial===null)this._equirectMaterial=QH(),this._compileMaterial(this._equirectMaterial)}dispose(){if(this._dispose(),this._cubemapMaterial!==null)this._cubemapMaterial.dispose();if(this._equirectMaterial!==null)this._equirectMaterial.dispose()}_setSize(J){this._lodMax=Math.floor(Math.log2(J)),this._cubeSize=Math.pow(2,this._lodMax)}_dispose(){if(this._blurMaterial!==null)this._blurMaterial.dispose();if(this._pingPongRenderTarget!==null)this._pingPongRenderTarget.dispose();for(let J=0;J<this._lodPlanes.length;J++)this._lodPlanes[J].dispose()}_cleanup(J){this._renderer.setRenderTarget(v$,f$,h$),this._renderer.xr.enabled=b$,J.scissorTest=!1,u7(J,0,0,J.width,J.height)}_fromTexture(J,Q){if(J.mapping===j9||J.mapping===W9)this._setSize(J.image.length===0?16:J.image[0].width||J.image[0].image.width);else this._setSize(J.image.width/4);v$=this._renderer.getRenderTarget(),f$=this._renderer.getActiveCubeFace(),h$=this._renderer.getActiveMipmapLevel(),b$=this._renderer.xr.enabled,this._renderer.xr.enabled=!1;let $=Q||this._allocateTargets();return this._textureToCubeUV(J,$),this._applyPMREM($),this._cleanup($),$}_allocateTargets(){let J=3*Math.max(this._cubeSize,112),Q=4*this._cubeSize,$={magFilter:Z8,minFilter:Z8,generateMipmaps:!1,type:G6,format:U8,colorSpace:P0,depthBuffer:!1},Z=JH(J,Q,$);if(this._pingPongRenderTarget===null||this._pingPongRenderTarget.width!==J||this._pingPongRenderTarget.height!==Q){if(this._pingPongRenderTarget!==null)this._dispose();this._pingPongRenderTarget=JH(J,Q,$);let{_lodMax:W}=this;({sizeLods:this._sizeLods,lodPlanes:this._lodPlanes,sigmas:this._sigmas}=ZG(W)),this._blurMaterial=WG(W,J,Q)}return Z}_compileMaterial(J){let Q=new C0(this._lodPlanes[0],J);this._renderer.compile(Q,y$)}_sceneToCubeUV(J,Q,$,Z,W){let X=new O0(90,1,Q,$),K=[1,-1,1,1,1,1],U=[1,1,1,-1,-1,-1],G=this._renderer,q=G.autoClear,E=G.toneMapping;if(G.getClearColor(tW),G.toneMapping=z8,G.autoClear=!1,G.state.buffers.depth.getReversed())G.setRenderTarget(Z),G.clearDepth(),G.setRenderTarget(null);let k=new G8({name:"PMREM.Background",side:b0,depthWrite:!1,depthTest:!1}),M=new C0(new x9,k),N=!1,O=J.background;if(O){if(O.isColor)k.color.copy(O),J.background=null,N=!0}else k.color.copy(tW),N=!0;for(let C=0;C<6;C++){let L=C%3;if(L===0)X.up.set(0,K[C],0),X.position.set(W.x,W.y,W.z),X.lookAt(W.x+U[C],W.y,W.z);else if(L===1)X.up.set(0,0,K[C]),X.position.set(W.x,W.y,W.z),X.lookAt(W.x,W.y+U[C],W.z);else X.up.set(0,K[C],0),X.position.set(W.x,W.y,W.z),X.lookAt(W.x,W.y,W.z+U[C]);let w=this._cubeSize;if(u7(Z,L*w,C>2?w:0,w,w),G.setRenderTarget(Z),N)G.render(M,X);G.render(J,X)}M.geometry.dispose(),M.material.dispose(),G.toneMapping=E,G.autoClear=q,J.background=O}_textureToCubeUV(J,Q){let $=this._renderer,Z=J.mapping===j9||J.mapping===W9;if(Z){if(this._cubemapMaterial===null)this._cubemapMaterial=$H();this._cubemapMaterial.uniforms.flipEnvMap.value=J.isRenderTargetTexture===!1?-1:1}else if(this._equirectMaterial===null)this._equirectMaterial=QH();let W=Z?this._cubemapMaterial:this._equirectMaterial,H=new C0(this._lodPlanes[0],W),Y=W.uniforms;Y.envMap.value=J;let X=this._cubeSize;u7(Q,0,0,3*X,2*X),$.setRenderTarget(Q),$.render(H,y$)}_applyPMREM(J){let Q=this._renderer,$=Q.autoClear;Q.autoClear=!1;let Z=this._lodPlanes.length;for(let W=1;W<Z;W++){let H=Math.sqrt(this._sigmas[W]*this._sigmas[W]-this._sigmas[W-1]*this._sigmas[W-1]),Y=eW[(Z-W-1)%eW.length];this._blur(J,W-1,W,H,Y)}Q.autoClear=$}_blur(J,Q,$,Z,W){let H=this._pingPongRenderTarget;this._halfBlur(J,H,Q,$,Z,"latitudinal",W),this._halfBlur(H,J,$,$,Z,"longitudinal",W)}_halfBlur(J,Q,$,Z,W,H,Y){let X=this._renderer,K=this._blurMaterial;if(H!=="latitudinal"&&H!=="longitudinal")console.error("blur direction must be either latitudinal or longitudinal!");let U=3,G=new C0(this._lodPlanes[Z],K),q=K.uniforms,E=this._sizeLods[$]-1,F=isFinite(W)?Math.PI/(2*E):2*Math.PI/(2*E9-1),k=W/F,M=isFinite(W)?1+Math.floor(U*k):E9;if(M>E9)console.warn(`sigmaRadians, ${W}, is too large and will clip, as it requested ${M} samples when the maximum is set to ${E9}`);let N=[],O=0;for(let _=0;_<E9;++_){let T=_/k,x=Math.exp(-T*T/2);if(N.push(x),_===0)O+=x;else if(_<M)O+=2*x}for(let _=0;_<N.length;_++)N[_]=N[_]/O;if(q.envMap.value=J.texture,q.samples.value=M,q.weights.value=N,q.latitudinal.value=H==="latitudinal",Y)q.poleAxis.value=Y;let{_lodMax:C}=this;q.dTheta.value=F,q.mipInt.value=C-$;let L=this._sizeLods[Z],w=3*L*(Z>C-n9?Z-C+n9:0),v=4*(this._cubeSize-L);u7(Q,w,v,3*L,2*L),X.setRenderTarget(Q),X.render(G,y$)}}function ZG(J){let Q=[],$=[],Z=[],W=J,H=J-n9+1+rW.length;for(let Y=0;Y<H;Y++){let X=Math.pow(2,W);$.push(X);let K=1/X;if(Y>J-n9)K=rW[Y-J+n9-1];else if(Y===0)K=0;Z.push(K);let U=1/(X-2),G=-U,q=1+U,E=[G,G,q,G,q,q,G,G,q,q,G,q],F=6,k=6,M=3,N=2,O=1,C=new Float32Array(M*k*F),L=new Float32Array(N*k*F),w=new Float32Array(O*k*F);for(let _=0;_<F;_++){let T=_%3*2/3-1,x=_>2?0:-1,z=[T,x,0,T+0.6666666666666666,x,0,T+0.6666666666666666,x+1,0,T,x,0,T+0.6666666666666666,x+1,0,T,x+1,0];C.set(z,M*k*_),L.set(E,N*k*_);let V=[_,_,_,_,_,_];w.set(V,O*k*_)}let v=new p0;if(v.setAttribute("position",new F0(C,M)),v.setAttribute("uv",new F0(L,N)),v.setAttribute("faceIndex",new F0(w,O)),Q.push(v),W>n9)W--}return{lodPlanes:Q,sizeLods:$,sigmas:Z}}function JH(J,Q,$){let Z=new _8(J,Q,$);return Z.texture.mapping=K6,Z.texture.name="PMREM.cubeUv",Z.scissorTest=!0,Z}function u7(J,Q,$,Z,W){J.viewport.set(Q,$,Z,W),J.scissor.set(Q,$,Z,W)}function WG(J,Q,$){let Z=new Float32Array(E9),W=new A(0,1,0);return new q8({name:"SphericalGaussianBlur",defines:{n:E9,CUBEUV_TEXEL_WIDTH:1/Q,CUBEUV_TEXEL_HEIGHT:1/$,CUBEUV_MAX_MIP:`${J}.0`},uniforms:{envMap:{value:null},samples:{value:1},weights:{value:Z},latitudinal:{value:!1},dTheta:{value:0},mipInt:{value:0},poleAxis:{value:W}},vertexShader:l$(),fragmentShader:`

			precision mediump float;
			precision mediump int;

			varying vec3 vOutputDirection;

			uniform sampler2D envMap;
			uniform int samples;
			uniform float weights[ n ];
			uniform bool latitudinal;
			uniform float dTheta;
			uniform float mipInt;
			uniform vec3 poleAxis;

			#define ENVMAP_TYPE_CUBE_UV
			#include <cube_uv_reflection_fragment>

			vec3 getSample( float theta, vec3 axis ) {

				float cosTheta = cos( theta );
				// Rodrigues' axis-angle rotation
				vec3 sampleDirection = vOutputDirection * cosTheta
					+ cross( axis, vOutputDirection ) * sin( theta )
					+ axis * dot( axis, vOutputDirection ) * ( 1.0 - cosTheta );

				return bilinearCubeUV( envMap, sampleDirection, mipInt );

			}

			void main() {

				vec3 axis = latitudinal ? poleAxis : cross( poleAxis, vOutputDirection );

				if ( all( equal( axis, vec3( 0.0 ) ) ) ) {

					axis = vec3( vOutputDirection.z, 0.0, - vOutputDirection.x );

				}

				axis = normalize( axis );

				gl_FragColor = vec4( 0.0, 0.0, 0.0, 1.0 );
				gl_FragColor.rgb += weights[ 0 ] * getSample( 0.0, axis );

				for ( int i = 1; i < n; i++ ) {

					if ( i >= samples ) {

						break;

					}

					float theta = dTheta * float( i );
					gl_FragColor.rgb += weights[ i ] * getSample( -1.0 * theta, axis );
					gl_FragColor.rgb += weights[ i ] * getSample( theta, axis );

				}

			}
		`,blending:g8,depthTest:!1,depthWrite:!1})}function QH(){return new q8({name:"EquirectangularToCubeUV",uniforms:{envMap:{value:null}},vertexShader:l$(),fragmentShader:`

			precision mediump float;
			precision mediump int;

			varying vec3 vOutputDirection;

			uniform sampler2D envMap;

			#include <common>

			void main() {

				vec3 outputDirection = normalize( vOutputDirection );
				vec2 uv = equirectUv( outputDirection );

				gl_FragColor = vec4( texture2D ( envMap, uv ).rgb, 1.0 );

			}
		`,blending:g8,depthTest:!1,depthWrite:!1})}function $H(){return new q8({name:"CubemapToCubeUV",uniforms:{envMap:{value:null},flipEnvMap:{value:-1}},vertexShader:l$(),fragmentShader:`

			precision mediump float;
			precision mediump int;

			uniform float flipEnvMap;

			varying vec3 vOutputDirection;

			uniform samplerCube envMap;

			void main() {

				gl_FragColor = textureCube( envMap, vec3( flipEnvMap * vOutputDirection.x, vOutputDirection.yz ) );

			}
		`,blending:g8,depthTest:!1,depthWrite:!1})}function l$(){return`

		precision mediump float;
		precision mediump int;

		attribute float faceIndex;

		varying vec3 vOutputDirection;

		// RH coordinate system; PMREM face-indexing convention
		vec3 getDirection( vec2 uv, float face ) {

			uv = 2.0 * uv - 1.0;

			vec3 direction = vec3( uv, 1.0 );

			if ( face == 0.0 ) {

				direction = direction.zyx; // ( 1, v, u ) pos x

			} else if ( face == 1.0 ) {

				direction = direction.xzy;
				direction.xz *= -1.0; // ( -u, 1, -v ) pos y

			} else if ( face == 2.0 ) {

				direction.x *= -1.0; // ( -u, v, 1 ) pos z

			} else if ( face == 3.0 ) {

				direction = direction.zyx;
				direction.xz *= -1.0; // ( -1, v, -u ) neg x

			} else if ( face == 4.0 ) {

				direction = direction.xzy;
				direction.xy *= -1.0; // ( -u, -1, v ) neg y

			} else if ( face == 5.0 ) {

				direction.z *= -1.0; // ( u, v, -1 ) neg z

			}

			return direction;

		}

		void main() {

			vOutputDirection = getDirection( uv, faceIndex );
			gl_Position = vec4( position, 1.0 );

		}
	`}function HG(J){let Q=new WeakMap,$=null;function Z(X){if(X&&X.isTexture){let K=X.mapping,U=K===K7||K===U7,G=K===j9||K===W9;if(U||G){let q=Q.get(X),E=q!==void 0?q.texture.pmremVersion:0;if(X.isRenderTargetTexture&&X.pmremVersion!==E){if($===null)$=new g$(J);return q=U?$.fromEquirectangular(X,q):$.fromCubemap(X,q),q.texture.pmremVersion=X.pmremVersion,Q.set(X,q),q.texture}else if(q!==void 0)return q.texture;else{let F=X.image;if(U&&F&&F.height>0||G&&F&&W(F)){if($===null)$=new g$(J);return q=U?$.fromEquirectangular(X):$.fromCubemap(X),q.texture.pmremVersion=X.pmremVersion,Q.set(X,q),X.addEventListener("dispose",H),q.texture}else return null}}}return X}function W(X){let K=0,U=6;for(let G=0;G<U;G++)if(X[G]!==void 0)K++;return K===U}function H(X){let K=X.target;K.removeEventListener("dispose",H);let U=Q.get(K);if(U!==void 0)Q.delete(K),U.dispose()}function Y(){if(Q=new WeakMap,$!==null)$.dispose(),$=null}return{get:Z,dispose:Y}}function YG(J){let Q={};function $(Z){if(Q[Z]!==void 0)return Q[Z];let W;switch(Z){case"WEBGL_depth_texture":W=J.getExtension("WEBGL_depth_texture")||J.getExtension("MOZ_WEBGL_depth_texture")||J.getExtension("WEBKIT_WEBGL_depth_texture");break;case"EXT_texture_filter_anisotropic":W=J.getExtension("EXT_texture_filter_anisotropic")||J.getExtension("MOZ_EXT_texture_filter_anisotropic")||J.getExtension("WEBKIT_EXT_texture_filter_anisotropic");break;case"WEBGL_compressed_texture_s3tc":W=J.getExtension("WEBGL_compressed_texture_s3tc")||J.getExtension("MOZ_WEBGL_compressed_texture_s3tc")||J.getExtension("WEBKIT_WEBGL_compressed_texture_s3tc");break;case"WEBGL_compressed_texture_pvrtc":W=J.getExtension("WEBGL_compressed_texture_pvrtc")||J.getExtension("WEBKIT_WEBGL_compressed_texture_pvrtc");break;default:W=J.getExtension(Z)}return Q[Z]=W,W}return{has:function(Z){return $(Z)!==null},init:function(){$("EXT_color_buffer_float"),$("WEBGL_clip_cull_distance"),$("OES_texture_float_linear"),$("EXT_color_buffer_half_float"),$("WEBGL_multisampled_render_to_texture"),$("WEBGL_render_shared_exponent")},get:function(Z){let W=$(Z);if(W===null)$9("THREE.WebGLRenderer: "+Z+" extension not supported.");return W}}}function XG(J,Q,$,Z){let W={},H=new WeakMap;function Y(q){let E=q.target;if(E.index!==null)Q.remove(E.index);for(let k in E.attributes)Q.remove(E.attributes[k]);E.removeEventListener("dispose",Y),delete W[E.id];let F=H.get(E);if(F)Q.remove(F),H.delete(E);if(Z.releaseStatesOfGeometry(E),E.isInstancedBufferGeometry===!0)delete E._maxInstanceCount;$.memory.geometries--}function X(q,E){if(W[E.id]===!0)return E;return E.addEventListener("dispose",Y),W[E.id]=!0,$.memory.geometries++,E}function K(q){let E=q.attributes;for(let F in E)Q.update(E[F],J.ARRAY_BUFFER)}function U(q){let E=[],F=q.index,k=q.attributes.position,M=0;if(F!==null){let C=F.array;M=F.version;for(let L=0,w=C.length;L<w;L+=3){let v=C[L+0],_=C[L+1],T=C[L+2];E.push(v,_,_,T,T,v)}}else if(k!==void 0){let C=k.array;M=k.version;for(let L=0,w=C.length/3-1;L<w;L+=3){let v=L+0,_=L+1,T=L+2;E.push(v,_,_,T,T,v)}}else return;let N=new((O$(E))?B7:z7)(E,1);N.version=M;let O=H.get(q);if(O)Q.remove(O);H.set(q,N)}function G(q){let E=H.get(q);if(E){let F=q.index;if(F!==null){if(E.version<F.version)U(q)}}else U(q);return H.get(q)}return{get:X,update:K,getWireframeAttribute:G}}function KG(J,Q,$){let Z;function W(E){Z=E}let H,Y;function X(E){H=E.type,Y=E.bytesPerElement}function K(E,F){J.drawElements(Z,F,H,E*Y),$.update(F,Z,1)}function U(E,F,k){if(k===0)return;J.drawElementsInstanced(Z,F,H,E*Y,k),$.update(F,Z,k)}function G(E,F,k){if(k===0)return;Q.get("WEBGL_multi_draw").multiDrawElementsWEBGL(Z,F,0,H,E,0,k);let N=0;for(let O=0;O<k;O++)N+=F[O];$.update(N,Z,1)}function q(E,F,k,M){if(k===0)return;let N=Q.get("WEBGL_multi_draw");if(N===null)for(let O=0;O<E.length;O++)U(E[O]/Y,F[O],M[O]);else{N.multiDrawElementsInstancedWEBGL(Z,F,0,H,E,0,M,0,k);let O=0;for(let C=0;C<k;C++)O+=F[C]*M[C];$.update(O,Z,1)}}this.setMode=W,this.setIndex=X,this.render=K,this.renderInstances=U,this.renderMultiDraw=G,this.renderMultiDrawInstances=q}function UG(J){let Q={geometries:0,textures:0},$={frame:0,calls:0,triangles:0,points:0,lines:0};function Z(H,Y,X){switch($.calls++,Y){case J.TRIANGLES:$.triangles+=X*(H/3);break;case J.LINES:$.lines+=X*(H/2);break;case J.LINE_STRIP:$.lines+=X*(H-1);break;case J.LINE_LOOP:$.lines+=X*H;break;case J.POINTS:$.points+=X*H;break;default:console.error("THREE.WebGLInfo: Unknown draw mode:",Y);break}}function W(){$.calls=0,$.triangles=0,$.points=0,$.lines=0}return{memory:Q,render:$,programs:null,autoReset:!0,reset:W,update:Z}}function GG(J,Q,$){let Z=new WeakMap,W=new sJ;function H(Y,X,K){let U=Y.morphTargetInfluences,G=X.morphAttributes.position||X.morphAttributes.normal||X.morphAttributes.color,q=G!==void 0?G.length:0,E=Z.get(X);if(E===void 0||E.count!==q){let z=function(){T.dispose(),Z.delete(X),X.removeEventListener("dispose",z)};if(E!==void 0)E.texture.dispose();let F=X.morphAttributes.position!==void 0,k=X.morphAttributes.normal!==void 0,M=X.morphAttributes.color!==void 0,N=X.morphAttributes.position||[],O=X.morphAttributes.normal||[],C=X.morphAttributes.color||[],L=0;if(F===!0)L=1;if(k===!0)L=2;if(M===!0)L=3;let w=X.attributes.position.count*L,v=1;if(w>Q.maxTextureSize)v=Math.ceil(w/Q.maxTextureSize),w=Q.maxTextureSize;let _=new Float32Array(w*v*4*q),T=new L7(_,w,v,q);T.type=l8,T.needsUpdate=!0;let x=L*4;for(let V=0;V<q;V++){let j=N[V],m=O[V],l=C[V],c=w*v*4*V;for(let i=0;i<j.count;i++){let u=i*x;if(F===!0)W.fromBufferAttribute(j,i),_[c+u+0]=W.x,_[c+u+1]=W.y,_[c+u+2]=W.z,_[c+u+3]=0;if(k===!0)W.fromBufferAttribute(m,i),_[c+u+4]=W.x,_[c+u+5]=W.y,_[c+u+6]=W.z,_[c+u+7]=0;if(M===!0)W.fromBufferAttribute(l,i),_[c+u+8]=W.x,_[c+u+9]=W.y,_[c+u+10]=W.z,_[c+u+11]=l.itemSize===4?W.w:1}}E={count:q,texture:T,size:new PJ(w,v)},Z.set(X,E),X.addEventListener("dispose",z)}if(Y.isInstancedMesh===!0&&Y.morphTexture!==null)K.getUniforms().setValue(J,"morphTexture",Y.morphTexture,$);else{let F=0;for(let M=0;M<U.length;M++)F+=U[M];let k=X.morphTargetsRelative?1:1-F;K.getUniforms().setValue(J,"morphTargetBaseInfluence",k),K.getUniforms().setValue(J,"morphTargetInfluences",U)}K.getUniforms().setValue(J,"morphTargetsTexture",E.texture,$),K.getUniforms().setValue(J,"morphTargetsTextureSize",E.size)}return{update:H}}function qG(J,Q,$,Z){let W=new WeakMap;function H(K){let U=Z.render.frame,G=K.geometry,q=Q.get(K,G);if(W.get(q)!==U)Q.update(q),W.set(q,U);if(K.isInstancedMesh){if(K.hasEventListener("dispose",X)===!1)K.addEventListener("dispose",X);if(W.get(K)!==U){if($.update(K.instanceMatrix,J.ARRAY_BUFFER),K.instanceColor!==null)$.update(K.instanceColor,J.ARRAY_BUFFER);W.set(K,U)}}if(K.isSkinnedMesh){let E=K.skeleton;if(W.get(E)!==U)E.update(),W.set(E,U)}return q}function Y(){W=new WeakMap}function X(K){let U=K.target;if(U.removeEventListener("dispose",X),$.remove(U.instanceMatrix),U.instanceColor!==null)$.remove(U.instanceColor)}return{update:H,dispose:Y}}var VH=new E0,ZH=new y7(1,1),zH=new L7,BH=new k$,CH=new w7,WH=[],HH=[],YH=new Float32Array(16),XH=new Float32Array(9),KH=new Float32Array(4);function s9(J,Q,$){let Z=J[0];if(Z<=0||Z>0)return J;let W=Q*$,H=WH[W];if(H===void 0)H=new Float32Array(W),WH[W]=H;if(Q!==0){Z.toArray(H,0);for(let Y=1,X=0;Y!==Q;++Y)X+=$,J[Y].toArray(H,X)}return H}function R0(J,Q){if(J.length!==Q.length)return!1;for(let $=0,Z=J.length;$<Z;$++)if(J[$]!==Q[$])return!1;return!0}function k0(J,Q){for(let $=0,Z=Q.length;$<Z;$++)J[$]=Q[$]}function n7(J,Q){let $=HH[Q];if($===void 0)$=new Int32Array(Q),HH[Q]=$;for(let Z=0;Z!==Q;++Z)$[Z]=J.allocateTextureUnit();return $}function EG(J,Q){let $=this.cache;if($[0]===Q)return;J.uniform1f(this.addr,Q),$[0]=Q}function NG(J,Q){let $=this.cache;if(Q.x!==void 0){if($[0]!==Q.x||$[1]!==Q.y)J.uniform2f(this.addr,Q.x,Q.y),$[0]=Q.x,$[1]=Q.y}else{if(R0($,Q))return;J.uniform2fv(this.addr,Q),k0($,Q)}}function OG(J,Q){let $=this.cache;if(Q.x!==void 0){if($[0]!==Q.x||$[1]!==Q.y||$[2]!==Q.z)J.uniform3f(this.addr,Q.x,Q.y,Q.z),$[0]=Q.x,$[1]=Q.y,$[2]=Q.z}else if(Q.r!==void 0){if($[0]!==Q.r||$[1]!==Q.g||$[2]!==Q.b)J.uniform3f(this.addr,Q.r,Q.g,Q.b),$[0]=Q.r,$[1]=Q.g,$[2]=Q.b}else{if(R0($,Q))return;J.uniform3fv(this.addr,Q),k0($,Q)}}function FG(J,Q){let $=this.cache;if(Q.x!==void 0){if($[0]!==Q.x||$[1]!==Q.y||$[2]!==Q.z||$[3]!==Q.w)J.uniform4f(this.addr,Q.x,Q.y,Q.z,Q.w),$[0]=Q.x,$[1]=Q.y,$[2]=Q.z,$[3]=Q.w}else{if(R0($,Q))return;J.uniform4fv(this.addr,Q),k0($,Q)}}function RG(J,Q){let $=this.cache,Z=Q.elements;if(Z===void 0){if(R0($,Q))return;J.uniformMatrix2fv(this.addr,!1,Q),k0($,Q)}else{if(R0($,Z))return;KH.set(Z),J.uniformMatrix2fv(this.addr,!1,KH),k0($,Z)}}function kG(J,Q){let $=this.cache,Z=Q.elements;if(Z===void 0){if(R0($,Q))return;J.uniformMatrix3fv(this.addr,!1,Q),k0($,Q)}else{if(R0($,Z))return;XH.set(Z),J.uniformMatrix3fv(this.addr,!1,XH),k0($,Z)}}function MG(J,Q){let $=this.cache,Z=Q.elements;if(Z===void 0){if(R0($,Q))return;J.uniformMatrix4fv(this.addr,!1,Q),k0($,Q)}else{if(R0($,Z))return;YH.set(Z),J.uniformMatrix4fv(this.addr,!1,YH),k0($,Z)}}function DG(J,Q){let $=this.cache;if($[0]===Q)return;J.uniform1i(this.addr,Q),$[0]=Q}function LG(J,Q){let $=this.cache;if(Q.x!==void 0){if($[0]!==Q.x||$[1]!==Q.y)J.uniform2i(this.addr,Q.x,Q.y),$[0]=Q.x,$[1]=Q.y}else{if(R0($,Q))return;J.uniform2iv(this.addr,Q),k0($,Q)}}function VG(J,Q){let $=this.cache;if(Q.x!==void 0){if($[0]!==Q.x||$[1]!==Q.y||$[2]!==Q.z)J.uniform3i(this.addr,Q.x,Q.y,Q.z),$[0]=Q.x,$[1]=Q.y,$[2]=Q.z}else{if(R0($,Q))return;J.uniform3iv(this.addr,Q),k0($,Q)}}function zG(J,Q){let $=this.cache;if(Q.x!==void 0){if($[0]!==Q.x||$[1]!==Q.y||$[2]!==Q.z||$[3]!==Q.w)J.uniform4i(this.addr,Q.x,Q.y,Q.z,Q.w),$[0]=Q.x,$[1]=Q.y,$[2]=Q.z,$[3]=Q.w}else{if(R0($,Q))return;J.uniform4iv(this.addr,Q),k0($,Q)}}function BG(J,Q){let $=this.cache;if($[0]===Q)return;J.uniform1ui(this.addr,Q),$[0]=Q}function CG(J,Q){let $=this.cache;if(Q.x!==void 0){if($[0]!==Q.x||$[1]!==Q.y)J.uniform2ui(this.addr,Q.x,Q.y),$[0]=Q.x,$[1]=Q.y}else{if(R0($,Q))return;J.uniform2uiv(this.addr,Q),k0($,Q)}}function wG(J,Q){let $=this.cache;if(Q.x!==void 0){if($[0]!==Q.x||$[1]!==Q.y||$[2]!==Q.z)J.uniform3ui(this.addr,Q.x,Q.y,Q.z),$[0]=Q.x,$[1]=Q.y,$[2]=Q.z}else{if(R0($,Q))return;J.uniform3uiv(this.addr,Q),k0($,Q)}}function _G(J,Q){let $=this.cache;if(Q.x!==void 0){if($[0]!==Q.x||$[1]!==Q.y||$[2]!==Q.z||$[3]!==Q.w)J.uniform4ui(this.addr,Q.x,Q.y,Q.z,Q.w),$[0]=Q.x,$[1]=Q.y,$[2]=Q.z,$[3]=Q.w}else{if(R0($,Q))return;J.uniform4uiv(this.addr,Q),k0($,Q)}}function IG(J,Q,$){let Z=this.cache,W=$.allocateTextureUnit();if(Z[0]!==W)J.uniform1i(this.addr,W),Z[0]=W;let H;if(this.type===J.SAMPLER_2D_SHADOW)ZH.compareFunction=G$,H=ZH;else H=VH;$.setTexture2D(Q||H,W)}function PG(J,Q,$){let Z=this.cache,W=$.allocateTextureUnit();if(Z[0]!==W)J.uniform1i(this.addr,W),Z[0]=W;$.setTexture3D(Q||BH,W)}function TG(J,Q,$){let Z=this.cache,W=$.allocateTextureUnit();if(Z[0]!==W)J.uniform1i(this.addr,W),Z[0]=W;$.setTextureCube(Q||CH,W)}function AG(J,Q,$){let Z=this.cache,W=$.allocateTextureUnit();if(Z[0]!==W)J.uniform1i(this.addr,W),Z[0]=W;$.setTexture2DArray(Q||zH,W)}function SG(J){switch(J){case 5126:return EG;case 35664:return NG;case 35665:return OG;case 35666:return FG;case 35674:return RG;case 35675:return kG;case 35676:return MG;case 5124:case 35670:return DG;case 35667:case 35671:return LG;case 35668:case 35672:return VG;case 35669:case 35673:return zG;case 5125:return BG;case 36294:return CG;case 36295:return wG;case 36296:return _G;case 35678:case 36198:case 36298:case 36306:case 35682:return IG;case 35679:case 36299:case 36307:return PG;case 35680:case 36300:case 36308:case 36293:return TG;case 36289:case 36303:case 36311:case 36292:return AG}}function jG(J,Q){J.uniform1fv(this.addr,Q)}function yG(J,Q){let $=s9(Q,this.size,2);J.uniform2fv(this.addr,$)}function vG(J,Q){let $=s9(Q,this.size,3);J.uniform3fv(this.addr,$)}function fG(J,Q){let $=s9(Q,this.size,4);J.uniform4fv(this.addr,$)}function hG(J,Q){let $=s9(Q,this.size,4);J.uniformMatrix2fv(this.addr,!1,$)}function bG(J,Q){let $=s9(Q,this.size,9);J.uniformMatrix3fv(this.addr,!1,$)}function xG(J,Q){let $=s9(Q,this.size,16);J.uniformMatrix4fv(this.addr,!1,$)}function gG(J,Q){J.uniform1iv(this.addr,Q)}function pG(J,Q){J.uniform2iv(this.addr,Q)}function lG(J,Q){J.uniform3iv(this.addr,Q)}function dG(J,Q){J.uniform4iv(this.addr,Q)}function mG(J,Q){J.uniform1uiv(this.addr,Q)}function uG(J,Q){J.uniform2uiv(this.addr,Q)}function cG(J,Q){J.uniform3uiv(this.addr,Q)}function nG(J,Q){J.uniform4uiv(this.addr,Q)}function sG(J,Q,$){let Z=this.cache,W=Q.length,H=n7($,W);if(!R0(Z,H))J.uniform1iv(this.addr,H),k0(Z,H);for(let Y=0;Y!==W;++Y)$.setTexture2D(Q[Y]||VH,H[Y])}function oG(J,Q,$){let Z=this.cache,W=Q.length,H=n7($,W);if(!R0(Z,H))J.uniform1iv(this.addr,H),k0(Z,H);for(let Y=0;Y!==W;++Y)$.setTexture3D(Q[Y]||BH,H[Y])}function iG(J,Q,$){let Z=this.cache,W=Q.length,H=n7($,W);if(!R0(Z,H))J.uniform1iv(this.addr,H),k0(Z,H);for(let Y=0;Y!==W;++Y)$.setTextureCube(Q[Y]||CH,H[Y])}function aG(J,Q,$){let Z=this.cache,W=Q.length,H=n7($,W);if(!R0(Z,H))J.uniform1iv(this.addr,H),k0(Z,H);for(let Y=0;Y!==W;++Y)$.setTexture2DArray(Q[Y]||zH,H[Y])}function rG(J){switch(J){case 5126:return jG;case 35664:return yG;case 35665:return vG;case 35666:return fG;case 35674:return hG;case 35675:return bG;case 35676:return xG;case 5124:case 35670:return gG;case 35667:case 35671:return pG;case 35668:case 35672:return lG;case 35669:case 35673:return dG;case 5125:return mG;case 36294:return uG;case 36295:return cG;case 36296:return nG;case 35678:case 36198:case 36298:case 36306:case 35682:return sG;case 35679:case 36299:case 36307:return oG;case 35680:case 36300:case 36308:case 36293:return iG;case 36289:case 36303:case 36311:case 36292:return aG}}class wH{constructor(J,Q,$){this.id=J,this.addr=$,this.cache=[],this.type=Q.type,this.setValue=SG(Q.type)}}class _H{constructor(J,Q,$){this.id=J,this.addr=$,this.cache=[],this.type=Q.type,this.size=Q.size,this.setValue=rG(Q.type)}}class IH{constructor(J){this.id=J,this.seq=[],this.map={}}setValue(J,Q,$){let Z=this.seq;for(let W=0,H=Z.length;W!==H;++W){let Y=Z[W];Y.setValue(J,Q[Y.id],$)}}}var x$=/(\w+)(\])?(\[|\.)?/g;function UH(J,Q){J.seq.push(Q),J.map[Q.id]=Q}function tG(J,Q,$){let Z=J.name,W=Z.length;x$.lastIndex=0;while(!0){let H=x$.exec(Z),Y=x$.lastIndex,X=H[1],K=H[2]==="]",U=H[3];if(K)X=X|0;if(U===void 0||U==="["&&Y+2===W){UH($,U===void 0?new wH(X,J,Q):new _H(X,J,Q));break}else{let q=$.map[X];if(q===void 0)q=new IH(X),UH($,q);$=q}}}class w6{constructor(J,Q){this.seq=[],this.map={};let $=J.getProgramParameter(Q,J.ACTIVE_UNIFORMS);for(let Z=0;Z<$;++Z){let W=J.getActiveUniform(Q,Z),H=J.getUniformLocation(Q,W.name);tG(W,H,this)}}setValue(J,Q,$,Z){let W=this.map[Q];if(W!==void 0)W.setValue(J,$,Z)}setOptional(J,Q,$){let Z=Q[$];if(Z!==void 0)this.setValue(J,$,Z)}static upload(J,Q,$,Z){for(let W=0,H=Q.length;W!==H;++W){let Y=Q[W],X=$[Y.id];if(X.needsUpdate!==!1)Y.setValue(J,X.value,Z)}}static seqWithValue(J,Q){let $=[];for(let Z=0,W=J.length;Z!==W;++Z){let H=J[Z];if(H.id in Q)$.push(H)}return $}}function GH(J,Q,$){let Z=J.createShader(Q);return J.shaderSource(Z,$),J.compileShader(Z),Z}var eG=37297,J1=0;function Q1(J,Q){let $=J.split(`
`),Z=[],W=Math.max(Q-6,0),H=Math.min(Q+6,$.length);for(let Y=W;Y<H;Y++){let X=Y+1;Z.push(`${X===Q?">":" "} ${X}: ${$[Y]}`)}return Z.join(`
`)}var qH=new fJ;function $1(J){lJ._getMatrix(qH,lJ.workingColorSpace,J);let Q=`mat3( ${qH.elements.map(($)=>$.toFixed(4))} )`;switch(lJ.getTransfer(J)){case U$:return[Q,"LinearTransferOETF"];case W0:return[Q,"sRGBTransferOETF"];default:return console.warn("THREE.WebGLProgram: Unsupported color space: ",J),[Q,"LinearTransferOETF"]}}function EH(J,Q,$){let Z=J.getShaderParameter(Q,J.COMPILE_STATUS),H=(J.getShaderInfoLog(Q)||"").trim();if(Z&&H==="")return"";let Y=/ERROR: 0:(\d+)/.exec(H);if(Y){let X=parseInt(Y[1]);return $.toUpperCase()+`

`+H+`

`+Q1(J.getShaderSource(Q),X)}else return H}function Z1(J,Q){let $=$1(Q);return[`vec4 ${J}( vec4 value ) {`,`	return ${$[1]}( vec4( value.rgb * ${$[0]}, value.a ) );`,"}"].join(`
`)}function W1(J,Q){let $;switch(Q){case FW:$="Linear";break;case RW:$="Reinhard";break;case kW:$="Cineon";break;case MW:$="ACESFilmic";break;case LW:$="AgX";break;case VW:$="Neutral";break;case DW:$="Custom";break;default:console.warn("THREE.WebGLProgram: Unsupported toneMapping:",Q),$="Linear"}return"vec3 "+J+"( vec3 color ) { return "+$+"ToneMapping( color ); }"}var c7=new A;function H1(){lJ.getLuminanceCoefficients(c7);let J=c7.x.toFixed(4),Q=c7.y.toFixed(4),$=c7.z.toFixed(4);return["float luminance( const in vec3 rgb ) {",`	const vec3 weights = vec3( ${J}, ${Q}, ${$} );`,"\treturn dot( weights, rgb );","}"].join(`
`)}function Y1(J){return[J.extensionClipCullDistance?"#extension GL_ANGLE_clip_cull_distance : require":"",J.extensionMultiDraw?"#extension GL_ANGLE_multi_draw : require":""].filter(C6).join(`
`)}function X1(J){let Q=[];for(let $ in J){let Z=J[$];if(Z===!1)continue;Q.push("#define "+$+" "+Z)}return Q.join(`
`)}function K1(J,Q){let $={},Z=J.getProgramParameter(Q,J.ACTIVE_ATTRIBUTES);for(let W=0;W<Z;W++){let H=J.getActiveAttrib(Q,W),Y=H.name,X=1;if(H.type===J.FLOAT_MAT2)X=2;if(H.type===J.FLOAT_MAT3)X=3;if(H.type===J.FLOAT_MAT4)X=4;$[Y]={type:H.type,location:J.getAttribLocation(Q,Y),locationSize:X}}return $}function C6(J){return J!==""}function NH(J,Q){let $=Q.numSpotLightShadows+Q.numSpotLightMaps-Q.numSpotLightShadowsWithMaps;return J.replace(/NUM_DIR_LIGHTS/g,Q.numDirLights).replace(/NUM_SPOT_LIGHTS/g,Q.numSpotLights).replace(/NUM_SPOT_LIGHT_MAPS/g,Q.numSpotLightMaps).replace(/NUM_SPOT_LIGHT_COORDS/g,$).replace(/NUM_RECT_AREA_LIGHTS/g,Q.numRectAreaLights).replace(/NUM_POINT_LIGHTS/g,Q.numPointLights).replace(/NUM_HEMI_LIGHTS/g,Q.numHemiLights).replace(/NUM_DIR_LIGHT_SHADOWS/g,Q.numDirLightShadows).replace(/NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS/g,Q.numSpotLightShadowsWithMaps).replace(/NUM_SPOT_LIGHT_SHADOWS/g,Q.numSpotLightShadows).replace(/NUM_POINT_LIGHT_SHADOWS/g,Q.numPointLightShadows)}function OH(J,Q){return J.replace(/NUM_CLIPPING_PLANES/g,Q.numClippingPlanes).replace(/UNION_CLIPPING_PLANES/g,Q.numClippingPlanes-Q.numClipIntersection)}var U1=/^[ \t]*#include +<([\w\d./]+)>/gm;function p$(J){return J.replace(U1,q1)}var G1=new Map;function q1(J,Q){let $=hJ[Q];if($===void 0){let Z=G1.get(Q);if(Z!==void 0)$=hJ[Z],console.warn('THREE.WebGLRenderer: Shader chunk "%s" has been deprecated. Use "%s" instead.',Q,Z);else throw new Error("Can not resolve #include <"+Q+">")}return p$($)}var E1=/#pragma unroll_loop_start\s+for\s*\(\s*int\s+i\s*=\s*(\d+)\s*;\s*i\s*<\s*(\d+)\s*;\s*i\s*\+\+\s*\)\s*{([\s\S]+?)}\s+#pragma unroll_loop_end/g;function FH(J){return J.replace(E1,N1)}function N1(J,Q,$,Z){let W="";for(let H=parseInt(Q);H<parseInt($);H++)W+=Z.replace(/\[\s*i\s*\]/g,"[ "+H+" ]").replace(/UNROLLED_LOOP_INDEX/g,H);return W}function RH(J){let Q=`precision ${J.precision} float;
	precision ${J.precision} int;
	precision ${J.precision} sampler2D;
	precision ${J.precision} samplerCube;
	precision ${J.precision} sampler3D;
	precision ${J.precision} sampler2DArray;
	precision ${J.precision} sampler2DShadow;
	precision ${J.precision} samplerCubeShadow;
	precision ${J.precision} sampler2DArrayShadow;
	precision ${J.precision} isampler2D;
	precision ${J.precision} isampler3D;
	precision ${J.precision} isamplerCube;
	precision ${J.precision} isampler2DArray;
	precision ${J.precision} usampler2D;
	precision ${J.precision} usampler3D;
	precision ${J.precision} usamplerCube;
	precision ${J.precision} usampler2DArray;
	`;if(J.precision==="highp")Q+=`
#define HIGH_PRECISION`;else if(J.precision==="mediump")Q+=`
#define MEDIUM_PRECISION`;else if(J.precision==="lowp")Q+=`
#define LOW_PRECISION`;return Q}function O1(J){let Q="SHADOWMAP_TYPE_BASIC";if(J.shadowMapType===wQ)Q="SHADOWMAP_TYPE_PCF";else if(J.shadowMapType===cZ)Q="SHADOWMAP_TYPE_PCF_SOFT";else if(J.shadowMapType===K8)Q="SHADOWMAP_TYPE_VSM";return Q}function F1(J){let Q="ENVMAP_TYPE_CUBE";if(J.envMap)switch(J.envMapMode){case j9:case W9:Q="ENVMAP_TYPE_CUBE";break;case K6:Q="ENVMAP_TYPE_CUBE_UV";break}return Q}function R1(J){let Q="ENVMAP_MODE_REFLECTION";if(J.envMap)switch(J.envMapMode){case W9:Q="ENVMAP_MODE_REFRACTION";break}return Q}function k1(J){let Q="ENVMAP_BLENDING_NONE";if(J.envMap)switch(J.combine){case EW:Q="ENVMAP_BLENDING_MULTIPLY";break;case NW:Q="ENVMAP_BLENDING_MIX";break;case OW:Q="ENVMAP_BLENDING_ADD";break}return Q}function M1(J){let Q=J.envMapCubeUVHeight;if(Q===null)return null;let $=Math.log2(Q)-2,Z=1/Q;return{texelWidth:1/(3*Math.max(Math.pow(2,$),112)),texelHeight:Z,maxMip:$}}function D1(J,Q,$,Z){let W=J.getContext(),H=$.defines,Y=$.vertexShader,X=$.fragmentShader,K=O1($),U=F1($),G=R1($),q=k1($),E=M1($),F=Y1($),k=X1(H),M=W.createProgram(),N,O,C=$.glslVersion?"#version "+$.glslVersion+`
`:"";if($.isRawShaderMaterial){if(N=["#define SHADER_TYPE "+$.shaderType,"#define SHADER_NAME "+$.shaderName,k].filter(C6).join(`
`),N.length>0)N+=`
`;if(O=["#define SHADER_TYPE "+$.shaderType,"#define SHADER_NAME "+$.shaderName,k].filter(C6).join(`
`),O.length>0)O+=`
`}else N=[RH($),"#define SHADER_TYPE "+$.shaderType,"#define SHADER_NAME "+$.shaderName,k,$.extensionClipCullDistance?"#define USE_CLIP_DISTANCE":"",$.batching?"#define USE_BATCHING":"",$.batchingColor?"#define USE_BATCHING_COLOR":"",$.instancing?"#define USE_INSTANCING":"",$.instancingColor?"#define USE_INSTANCING_COLOR":"",$.instancingMorph?"#define USE_INSTANCING_MORPH":"",$.useFog&&$.fog?"#define USE_FOG":"",$.useFog&&$.fogExp2?"#define FOG_EXP2":"",$.map?"#define USE_MAP":"",$.envMap?"#define USE_ENVMAP":"",$.envMap?"#define "+G:"",$.lightMap?"#define USE_LIGHTMAP":"",$.aoMap?"#define USE_AOMAP":"",$.bumpMap?"#define USE_BUMPMAP":"",$.normalMap?"#define USE_NORMALMAP":"",$.normalMapObjectSpace?"#define USE_NORMALMAP_OBJECTSPACE":"",$.normalMapTangentSpace?"#define USE_NORMALMAP_TANGENTSPACE":"",$.displacementMap?"#define USE_DISPLACEMENTMAP":"",$.emissiveMap?"#define USE_EMISSIVEMAP":"",$.anisotropy?"#define USE_ANISOTROPY":"",$.anisotropyMap?"#define USE_ANISOTROPYMAP":"",$.clearcoatMap?"#define USE_CLEARCOATMAP":"",$.clearcoatRoughnessMap?"#define USE_CLEARCOAT_ROUGHNESSMAP":"",$.clearcoatNormalMap?"#define USE_CLEARCOAT_NORMALMAP":"",$.iridescenceMap?"#define USE_IRIDESCENCEMAP":"",$.iridescenceThicknessMap?"#define USE_IRIDESCENCE_THICKNESSMAP":"",$.specularMap?"#define USE_SPECULARMAP":"",$.specularColorMap?"#define USE_SPECULAR_COLORMAP":"",$.specularIntensityMap?"#define USE_SPECULAR_INTENSITYMAP":"",$.roughnessMap?"#define USE_ROUGHNESSMAP":"",$.metalnessMap?"#define USE_METALNESSMAP":"",$.alphaMap?"#define USE_ALPHAMAP":"",$.alphaHash?"#define USE_ALPHAHASH":"",$.transmission?"#define USE_TRANSMISSION":"",$.transmissionMap?"#define USE_TRANSMISSIONMAP":"",$.thicknessMap?"#define USE_THICKNESSMAP":"",$.sheenColorMap?"#define USE_SHEEN_COLORMAP":"",$.sheenRoughnessMap?"#define USE_SHEEN_ROUGHNESSMAP":"",$.mapUv?"#define MAP_UV "+$.mapUv:"",$.alphaMapUv?"#define ALPHAMAP_UV "+$.alphaMapUv:"",$.lightMapUv?"#define LIGHTMAP_UV "+$.lightMapUv:"",$.aoMapUv?"#define AOMAP_UV "+$.aoMapUv:"",$.emissiveMapUv?"#define EMISSIVEMAP_UV "+$.emissiveMapUv:"",$.bumpMapUv?"#define BUMPMAP_UV "+$.bumpMapUv:"",$.normalMapUv?"#define NORMALMAP_UV "+$.normalMapUv:"",$.displacementMapUv?"#define DISPLACEMENTMAP_UV "+$.displacementMapUv:"",$.metalnessMapUv?"#define METALNESSMAP_UV "+$.metalnessMapUv:"",$.roughnessMapUv?"#define ROUGHNESSMAP_UV "+$.roughnessMapUv:"",$.anisotropyMapUv?"#define ANISOTROPYMAP_UV "+$.anisotropyMapUv:"",$.clearcoatMapUv?"#define CLEARCOATMAP_UV "+$.clearcoatMapUv:"",$.clearcoatNormalMapUv?"#define CLEARCOAT_NORMALMAP_UV "+$.clearcoatNormalMapUv:"",$.clearcoatRoughnessMapUv?"#define CLEARCOAT_ROUGHNESSMAP_UV "+$.clearcoatRoughnessMapUv:"",$.iridescenceMapUv?"#define IRIDESCENCEMAP_UV "+$.iridescenceMapUv:"",$.iridescenceThicknessMapUv?"#define IRIDESCENCE_THICKNESSMAP_UV "+$.iridescenceThicknessMapUv:"",$.sheenColorMapUv?"#define SHEEN_COLORMAP_UV "+$.sheenColorMapUv:"",$.sheenRoughnessMapUv?"#define SHEEN_ROUGHNESSMAP_UV "+$.sheenRoughnessMapUv:"",$.specularMapUv?"#define SPECULARMAP_UV "+$.specularMapUv:"",$.specularColorMapUv?"#define SPECULAR_COLORMAP_UV "+$.specularColorMapUv:"",$.specularIntensityMapUv?"#define SPECULAR_INTENSITYMAP_UV "+$.specularIntensityMapUv:"",$.transmissionMapUv?"#define TRANSMISSIONMAP_UV "+$.transmissionMapUv:"",$.thicknessMapUv?"#define THICKNESSMAP_UV "+$.thicknessMapUv:"",$.vertexTangents&&$.flatShading===!1?"#define USE_TANGENT":"",$.vertexColors?"#define USE_COLOR":"",$.vertexAlphas?"#define USE_COLOR_ALPHA":"",$.vertexUv1s?"#define USE_UV1":"",$.vertexUv2s?"#define USE_UV2":"",$.vertexUv3s?"#define USE_UV3":"",$.pointsUvs?"#define USE_POINTS_UV":"",$.flatShading?"#define FLAT_SHADED":"",$.skinning?"#define USE_SKINNING":"",$.morphTargets?"#define USE_MORPHTARGETS":"",$.morphNormals&&$.flatShading===!1?"#define USE_MORPHNORMALS":"",$.morphColors?"#define USE_MORPHCOLORS":"",$.morphTargetsCount>0?"#define MORPHTARGETS_TEXTURE_STRIDE "+$.morphTextureStride:"",$.morphTargetsCount>0?"#define MORPHTARGETS_COUNT "+$.morphTargetsCount:"",$.doubleSided?"#define DOUBLE_SIDED":"",$.flipSided?"#define FLIP_SIDED":"",$.shadowMapEnabled?"#define USE_SHADOWMAP":"",$.shadowMapEnabled?"#define "+K:"",$.sizeAttenuation?"#define USE_SIZEATTENUATION":"",$.numLightProbes>0?"#define USE_LIGHT_PROBES":"",$.logarithmicDepthBuffer?"#define USE_LOGDEPTHBUF":"",$.reversedDepthBuffer?"#define USE_REVERSEDEPTHBUF":"","uniform mat4 modelMatrix;","uniform mat4 modelViewMatrix;","uniform mat4 projectionMatrix;","uniform mat4 viewMatrix;","uniform mat3 normalMatrix;","uniform vec3 cameraPosition;","uniform bool isOrthographic;","#ifdef USE_INSTANCING","\tattribute mat4 instanceMatrix;","#endif","#ifdef USE_INSTANCING_COLOR","\tattribute vec3 instanceColor;","#endif","#ifdef USE_INSTANCING_MORPH","\tuniform sampler2D morphTexture;","#endif","attribute vec3 position;","attribute vec3 normal;","attribute vec2 uv;","#ifdef USE_UV1","\tattribute vec2 uv1;","#endif","#ifdef USE_UV2","\tattribute vec2 uv2;","#endif","#ifdef USE_UV3","\tattribute vec2 uv3;","#endif","#ifdef USE_TANGENT","\tattribute vec4 tangent;","#endif","#if defined( USE_COLOR_ALPHA )","\tattribute vec4 color;","#elif defined( USE_COLOR )","\tattribute vec3 color;","#endif","#ifdef USE_SKINNING","\tattribute vec4 skinIndex;","\tattribute vec4 skinWeight;","#endif",`
`].filter(C6).join(`
`),O=[RH($),"#define SHADER_TYPE "+$.shaderType,"#define SHADER_NAME "+$.shaderName,k,$.useFog&&$.fog?"#define USE_FOG":"",$.useFog&&$.fogExp2?"#define FOG_EXP2":"",$.alphaToCoverage?"#define ALPHA_TO_COVERAGE":"",$.map?"#define USE_MAP":"",$.matcap?"#define USE_MATCAP":"",$.envMap?"#define USE_ENVMAP":"",$.envMap?"#define "+U:"",$.envMap?"#define "+G:"",$.envMap?"#define "+q:"",E?"#define CUBEUV_TEXEL_WIDTH "+E.texelWidth:"",E?"#define CUBEUV_TEXEL_HEIGHT "+E.texelHeight:"",E?"#define CUBEUV_MAX_MIP "+E.maxMip+".0":"",$.lightMap?"#define USE_LIGHTMAP":"",$.aoMap?"#define USE_AOMAP":"",$.bumpMap?"#define USE_BUMPMAP":"",$.normalMap?"#define USE_NORMALMAP":"",$.normalMapObjectSpace?"#define USE_NORMALMAP_OBJECTSPACE":"",$.normalMapTangentSpace?"#define USE_NORMALMAP_TANGENTSPACE":"",$.emissiveMap?"#define USE_EMISSIVEMAP":"",$.anisotropy?"#define USE_ANISOTROPY":"",$.anisotropyMap?"#define USE_ANISOTROPYMAP":"",$.clearcoat?"#define USE_CLEARCOAT":"",$.clearcoatMap?"#define USE_CLEARCOATMAP":"",$.clearcoatRoughnessMap?"#define USE_CLEARCOAT_ROUGHNESSMAP":"",$.clearcoatNormalMap?"#define USE_CLEARCOAT_NORMALMAP":"",$.dispersion?"#define USE_DISPERSION":"",$.iridescence?"#define USE_IRIDESCENCE":"",$.iridescenceMap?"#define USE_IRIDESCENCEMAP":"",$.iridescenceThicknessMap?"#define USE_IRIDESCENCE_THICKNESSMAP":"",$.specularMap?"#define USE_SPECULARMAP":"",$.specularColorMap?"#define USE_SPECULAR_COLORMAP":"",$.specularIntensityMap?"#define USE_SPECULAR_INTENSITYMAP":"",$.roughnessMap?"#define USE_ROUGHNESSMAP":"",$.metalnessMap?"#define USE_METALNESSMAP":"",$.alphaMap?"#define USE_ALPHAMAP":"",$.alphaTest?"#define USE_ALPHATEST":"",$.alphaHash?"#define USE_ALPHAHASH":"",$.sheen?"#define USE_SHEEN":"",$.sheenColorMap?"#define USE_SHEEN_COLORMAP":"",$.sheenRoughnessMap?"#define USE_SHEEN_ROUGHNESSMAP":"",$.transmission?"#define USE_TRANSMISSION":"",$.transmissionMap?"#define USE_TRANSMISSIONMAP":"",$.thicknessMap?"#define USE_THICKNESSMAP":"",$.vertexTangents&&$.flatShading===!1?"#define USE_TANGENT":"",$.vertexColors||$.instancingColor||$.batchingColor?"#define USE_COLOR":"",$.vertexAlphas?"#define USE_COLOR_ALPHA":"",$.vertexUv1s?"#define USE_UV1":"",$.vertexUv2s?"#define USE_UV2":"",$.vertexUv3s?"#define USE_UV3":"",$.pointsUvs?"#define USE_POINTS_UV":"",$.gradientMap?"#define USE_GRADIENTMAP":"",$.flatShading?"#define FLAT_SHADED":"",$.doubleSided?"#define DOUBLE_SIDED":"",$.flipSided?"#define FLIP_SIDED":"",$.shadowMapEnabled?"#define USE_SHADOWMAP":"",$.shadowMapEnabled?"#define "+K:"",$.premultipliedAlpha?"#define PREMULTIPLIED_ALPHA":"",$.numLightProbes>0?"#define USE_LIGHT_PROBES":"",$.decodeVideoTexture?"#define DECODE_VIDEO_TEXTURE":"",$.decodeVideoTextureEmissive?"#define DECODE_VIDEO_TEXTURE_EMISSIVE":"",$.logarithmicDepthBuffer?"#define USE_LOGDEPTHBUF":"",$.reversedDepthBuffer?"#define USE_REVERSEDEPTHBUF":"","uniform mat4 viewMatrix;","uniform vec3 cameraPosition;","uniform bool isOrthographic;",$.toneMapping!==z8?"#define TONE_MAPPING":"",$.toneMapping!==z8?hJ.tonemapping_pars_fragment:"",$.toneMapping!==z8?W1("toneMapping",$.toneMapping):"",$.dithering?"#define DITHERING":"",$.opaque?"#define OPAQUE":"",hJ.colorspace_pars_fragment,Z1("linearToOutputTexel",$.outputColorSpace),H1(),$.useDepthPacking?"#define DEPTH_PACKING "+$.depthPacking:"",`
`].filter(C6).join(`
`);if(Y=p$(Y),Y=NH(Y,$),Y=OH(Y,$),X=p$(X),X=NH(X,$),X=OH(X,$),Y=FH(Y),X=FH(X),$.isRawShaderMaterial!==!0)C=`#version 300 es
`,N=[F,"#define attribute in","#define varying out","#define texture2D texture"].join(`
`)+`
`+N,O=["#define varying in",$.glslVersion===q$?"":"layout(location = 0) out highp vec4 pc_fragColor;",$.glslVersion===q$?"":"#define gl_FragColor pc_fragColor","#define gl_FragDepthEXT gl_FragDepth","#define texture2D texture","#define textureCube texture","#define texture2DProj textureProj","#define texture2DLodEXT textureLod","#define texture2DProjLodEXT textureProjLod","#define textureCubeLodEXT textureLod","#define texture2DGradEXT textureGrad","#define texture2DProjGradEXT textureProjGrad","#define textureCubeGradEXT textureGrad"].join(`
`)+`
`+O;let L=C+N+Y,w=C+O+X,v=GH(W,W.VERTEX_SHADER,L),_=GH(W,W.FRAGMENT_SHADER,w);if(W.attachShader(M,v),W.attachShader(M,_),$.index0AttributeName!==void 0)W.bindAttribLocation(M,0,$.index0AttributeName);else if($.morphTargets===!0)W.bindAttribLocation(M,0,"position");W.linkProgram(M);function T(j){if(J.debug.checkShaderErrors){let m=W.getProgramInfoLog(M)||"",l=W.getShaderInfoLog(v)||"",c=W.getShaderInfoLog(_)||"",i=m.trim(),u=l.trim(),r=c.trim(),g=!0,ZJ=!0;if(W.getProgramParameter(M,W.LINK_STATUS)===!1)if(g=!1,typeof J.debug.onShaderError==="function")J.debug.onShaderError(W,M,v,_);else{let UJ=EH(W,v,"vertex"),TJ=EH(W,_,"fragment");console.error("THREE.WebGLProgram: Shader Error "+W.getError()+" - VALIDATE_STATUS "+W.getProgramParameter(M,W.VALIDATE_STATUS)+`

Material Name: `+j.name+`
Material Type: `+j.type+`

Program Info Log: `+i+`
`+UJ+`
`+TJ)}else if(i!=="")console.warn("THREE.WebGLProgram: Program Info Log:",i);else if(u===""||r==="")ZJ=!1;if(ZJ)j.diagnostics={runnable:g,programLog:i,vertexShader:{log:u,prefix:N},fragmentShader:{log:r,prefix:O}}}W.deleteShader(v),W.deleteShader(_),x=new w6(W,M),z=K1(W,M)}let x;this.getUniforms=function(){if(x===void 0)T(this);return x};let z;this.getAttributes=function(){if(z===void 0)T(this);return z};let V=$.rendererExtensionParallelShaderCompile===!1;return this.isReady=function(){if(V===!1)V=W.getProgramParameter(M,eG);return V},this.destroy=function(){Z.releaseStatesOfProgram(this),W.deleteProgram(M),this.program=void 0},this.type=$.shaderType,this.name=$.shaderName,this.id=J1++,this.cacheKey=Q,this.usedTimes=1,this.program=M,this.vertexShader=v,this.fragmentShader=_,this}var L1=0;class PH{constructor(){this.shaderCache=new Map,this.materialCache=new Map}update(J){let{vertexShader:Q,fragmentShader:$}=J,Z=this._getShaderStage(Q),W=this._getShaderStage($),H=this._getShaderCacheForMaterial(J);if(H.has(Z)===!1)H.add(Z),Z.usedTimes++;if(H.has(W)===!1)H.add(W),W.usedTimes++;return this}remove(J){let Q=this.materialCache.get(J);for(let $ of Q)if($.usedTimes--,$.usedTimes===0)this.shaderCache.delete($.code);return this.materialCache.delete(J),this}getVertexShaderID(J){return this._getShaderStage(J.vertexShader).id}getFragmentShaderID(J){return this._getShaderStage(J.fragmentShader).id}dispose(){this.shaderCache.clear(),this.materialCache.clear()}_getShaderCacheForMaterial(J){let Q=this.materialCache,$=Q.get(J);if($===void 0)$=new Set,Q.set(J,$);return $}_getShaderStage(J){let Q=this.shaderCache,$=Q.get(J);if($===void 0)$=new TH(J),Q.set(J,$);return $}}class TH{constructor(J){this.id=L1++,this.code=J,this.usedTimes=0}}function V1(J,Q,$,Z,W,H,Y){let X=new V7,K=new PH,U=new Set,G=[],q=W.logarithmicDepthBuffer,E=W.vertexTextures,F=W.precision,k={MeshDepthMaterial:"depth",MeshDistanceMaterial:"distanceRGBA",MeshNormalMaterial:"normal",MeshBasicMaterial:"basic",MeshLambertMaterial:"lambert",MeshPhongMaterial:"phong",MeshToonMaterial:"toon",MeshStandardMaterial:"physical",MeshPhysicalMaterial:"physical",MeshMatcapMaterial:"matcap",LineBasicMaterial:"basic",LineDashedMaterial:"dashed",PointsMaterial:"points",ShadowMaterial:"shadow",SpriteMaterial:"sprite"};function M(z){if(U.add(z),z===0)return"uv";return`uv${z}`}function N(z,V,j,m,l){let c=m.fog,i=l.geometry,u=z.isMeshStandardMaterial?m.environment:null,r=(z.isMeshStandardMaterial?$:Q).get(z.envMap||u),g=!!r&&r.mapping===K6?r.image.height:null,ZJ=k[z.type];if(z.precision!==null){if(F=W.getMaxPrecision(z.precision),F!==z.precision)console.warn("THREE.WebGLProgram.getParameters:",z.precision,"not supported, using",F,"instead.")}let UJ=i.morphAttributes.position||i.morphAttributes.normal||i.morphAttributes.color,TJ=UJ!==void 0?UJ.length:0,mJ=0;if(i.morphAttributes.position!==void 0)mJ=1;if(i.morphAttributes.normal!==void 0)mJ=2;if(i.morphAttributes.color!==void 0)mJ=3;let Y0,d,WJ,MJ;if(ZJ){let rJ=E8[ZJ];Y0=rJ.vertexShader,d=rJ.fragmentShader}else Y0=z.vertexShader,d=z.fragmentShader,K.update(z),WJ=K.getVertexShaderID(z),MJ=K.getFragmentShaderID(z);let GJ=J.getRenderTarget(),RJ=J.state.buffers.depth.getReversed(),uJ=l.isInstancedMesh===!0,cJ=l.isBatchedMesh===!0,dJ=!!z.map,I=!!z.matcap,$0=!!r,CJ=!!z.aoMap,iJ=!!z.lightMap,zJ=!!z.bumpMap,X0=!!z.normalMap,DJ=!!z.displacementMap,_J=!!z.emissiveMap,V0=!!z.metalnessMap,D0=!!z.roughnessMap,N0=z.anisotropy>0,B=z.clearcoat>0,R=z.dispersion>0,f=z.iridescence>0,n=z.sheen>0,o=z.transmission>0,p=N0&&!!z.anisotropyMap,EJ=B&&!!z.clearcoatMap,JJ=B&&!!z.clearcoatNormalMap,kJ=B&&!!z.clearcoatRoughnessMap,AJ=f&&!!z.iridescenceMap,e=f&&!!z.iridescenceThicknessMap,XJ=n&&!!z.sheenColorMap,LJ=n&&!!z.sheenRoughnessMap,VJ=!!z.specularMap,KJ=!!z.specularColorMap,bJ=!!z.specularIntensityMap,P=o&&!!z.transmissionMap,HJ=o&&!!z.thicknessMap,QJ=!!z.gradientMap,NJ=!!z.alphaMap,a=z.alphaTest>0,s=!!z.alphaHash,FJ=!!z.extensions,yJ=z8;if(z.toneMapped){if(GJ===null||GJ.isXRRenderTarget===!0)yJ=J.toneMapping}let J0={shaderID:ZJ,shaderType:z.type,shaderName:z.name,vertexShader:Y0,fragmentShader:d,defines:z.defines,customVertexShaderID:WJ,customFragmentShaderID:MJ,isRawShaderMaterial:z.isRawShaderMaterial===!0,glslVersion:z.glslVersion,precision:F,batching:cJ,batchingColor:cJ&&l._colorsTexture!==null,instancing:uJ,instancingColor:uJ&&l.instanceColor!==null,instancingMorph:uJ&&l.morphTexture!==null,supportsVertexTextures:E,outputColorSpace:GJ===null?J.outputColorSpace:GJ.isXRRenderTarget===!0?GJ.texture.colorSpace:P0,alphaToCoverage:!!z.alphaToCoverage,map:dJ,matcap:I,envMap:$0,envMapMode:$0&&r.mapping,envMapCubeUVHeight:g,aoMap:CJ,lightMap:iJ,bumpMap:zJ,normalMap:X0,displacementMap:E&&DJ,emissiveMap:_J,normalMapObjectSpace:X0&&z.normalMapType===jW,normalMapTangentSpace:X0&&z.normalMapType===SW,metalnessMap:V0,roughnessMap:D0,anisotropy:N0,anisotropyMap:p,clearcoat:B,clearcoatMap:EJ,clearcoatNormalMap:JJ,clearcoatRoughnessMap:kJ,dispersion:R,iridescence:f,iridescenceMap:AJ,iridescenceThicknessMap:e,sheen:n,sheenColorMap:XJ,sheenRoughnessMap:LJ,specularMap:VJ,specularColorMap:KJ,specularIntensityMap:bJ,transmission:o,transmissionMap:P,thicknessMap:HJ,gradientMap:QJ,opaque:z.transparent===!1&&z.blending===Y6&&z.alphaToCoverage===!1,alphaMap:NJ,alphaTest:a,alphaHash:s,combine:z.combine,mapUv:dJ&&M(z.map.channel),aoMapUv:CJ&&M(z.aoMap.channel),lightMapUv:iJ&&M(z.lightMap.channel),bumpMapUv:zJ&&M(z.bumpMap.channel),normalMapUv:X0&&M(z.normalMap.channel),displacementMapUv:DJ&&M(z.displacementMap.channel),emissiveMapUv:_J&&M(z.emissiveMap.channel),metalnessMapUv:V0&&M(z.metalnessMap.channel),roughnessMapUv:D0&&M(z.roughnessMap.channel),anisotropyMapUv:p&&M(z.anisotropyMap.channel),clearcoatMapUv:EJ&&M(z.clearcoatMap.channel),clearcoatNormalMapUv:JJ&&M(z.clearcoatNormalMap.channel),clearcoatRoughnessMapUv:kJ&&M(z.clearcoatRoughnessMap.channel),iridescenceMapUv:AJ&&M(z.iridescenceMap.channel),iridescenceThicknessMapUv:e&&M(z.iridescenceThicknessMap.channel),sheenColorMapUv:XJ&&M(z.sheenColorMap.channel),sheenRoughnessMapUv:LJ&&M(z.sheenRoughnessMap.channel),specularMapUv:VJ&&M(z.specularMap.channel),specularColorMapUv:KJ&&M(z.specularColorMap.channel),specularIntensityMapUv:bJ&&M(z.specularIntensityMap.channel),transmissionMapUv:P&&M(z.transmissionMap.channel),thicknessMapUv:HJ&&M(z.thicknessMap.channel),alphaMapUv:NJ&&M(z.alphaMap.channel),vertexTangents:!!i.attributes.tangent&&(X0||N0),vertexColors:z.vertexColors,vertexAlphas:z.vertexColors===!0&&!!i.attributes.color&&i.attributes.color.itemSize===4,pointsUvs:l.isPoints===!0&&!!i.attributes.uv&&(dJ||NJ),fog:!!c,useFog:z.fog===!0,fogExp2:!!c&&c.isFogExp2,flatShading:z.flatShading===!0&&z.wireframe===!1,sizeAttenuation:z.sizeAttenuation===!0,logarithmicDepthBuffer:q,reversedDepthBuffer:RJ,skinning:l.isSkinnedMesh===!0,morphTargets:i.morphAttributes.position!==void 0,morphNormals:i.morphAttributes.normal!==void 0,morphColors:i.morphAttributes.color!==void 0,morphTargetsCount:TJ,morphTextureStride:mJ,numDirLights:V.directional.length,numPointLights:V.point.length,numSpotLights:V.spot.length,numSpotLightMaps:V.spotLightMap.length,numRectAreaLights:V.rectArea.length,numHemiLights:V.hemi.length,numDirLightShadows:V.directionalShadowMap.length,numPointLightShadows:V.pointShadowMap.length,numSpotLightShadows:V.spotShadowMap.length,numSpotLightShadowsWithMaps:V.numSpotLightShadowsWithMaps,numLightProbes:V.numLightProbes,numClippingPlanes:Y.numPlanes,numClipIntersection:Y.numIntersection,dithering:z.dithering,shadowMapEnabled:J.shadowMap.enabled&&j.length>0,shadowMapType:J.shadowMap.type,toneMapping:yJ,decodeVideoTexture:dJ&&z.map.isVideoTexture===!0&&lJ.getTransfer(z.map.colorSpace)===W0,decodeVideoTextureEmissive:_J&&z.emissiveMap.isVideoTexture===!0&&lJ.getTransfer(z.emissiveMap.colorSpace)===W0,premultipliedAlpha:z.premultipliedAlpha,doubleSided:z.side===o0,flipSided:z.side===b0,useDepthPacking:z.depthPacking>=0,depthPacking:z.depthPacking||0,index0AttributeName:z.index0AttributeName,extensionClipCullDistance:FJ&&z.extensions.clipCullDistance===!0&&Z.has("WEBGL_clip_cull_distance"),extensionMultiDraw:(FJ&&z.extensions.multiDraw===!0||cJ)&&Z.has("WEBGL_multi_draw"),rendererExtensionParallelShaderCompile:Z.has("KHR_parallel_shader_compile"),customProgramCacheKey:z.customProgramCacheKey()};return J0.vertexUv1s=U.has(1),J0.vertexUv2s=U.has(2),J0.vertexUv3s=U.has(3),U.clear(),J0}function O(z){let V=[];if(z.shaderID)V.push(z.shaderID);else V.push(z.customVertexShaderID),V.push(z.customFragmentShaderID);if(z.defines!==void 0)for(let j in z.defines)V.push(j),V.push(z.defines[j]);if(z.isRawShaderMaterial===!1)C(V,z),L(V,z),V.push(J.outputColorSpace);return V.push(z.customProgramCacheKey),V.join()}function C(z,V){z.push(V.precision),z.push(V.outputColorSpace),z.push(V.envMapMode),z.push(V.envMapCubeUVHeight),z.push(V.mapUv),z.push(V.alphaMapUv),z.push(V.lightMapUv),z.push(V.aoMapUv),z.push(V.bumpMapUv),z.push(V.normalMapUv),z.push(V.displacementMapUv),z.push(V.emissiveMapUv),z.push(V.metalnessMapUv),z.push(V.roughnessMapUv),z.push(V.anisotropyMapUv),z.push(V.clearcoatMapUv),z.push(V.clearcoatNormalMapUv),z.push(V.clearcoatRoughnessMapUv),z.push(V.iridescenceMapUv),z.push(V.iridescenceThicknessMapUv),z.push(V.sheenColorMapUv),z.push(V.sheenRoughnessMapUv),z.push(V.specularMapUv),z.push(V.specularColorMapUv),z.push(V.specularIntensityMapUv),z.push(V.transmissionMapUv),z.push(V.thicknessMapUv),z.push(V.combine),z.push(V.fogExp2),z.push(V.sizeAttenuation),z.push(V.morphTargetsCount),z.push(V.morphAttributeCount),z.push(V.numDirLights),z.push(V.numPointLights),z.push(V.numSpotLights),z.push(V.numSpotLightMaps),z.push(V.numHemiLights),z.push(V.numRectAreaLights),z.push(V.numDirLightShadows),z.push(V.numPointLightShadows),z.push(V.numSpotLightShadows),z.push(V.numSpotLightShadowsWithMaps),z.push(V.numLightProbes),z.push(V.shadowMapType),z.push(V.toneMapping),z.push(V.numClippingPlanes),z.push(V.numClipIntersection),z.push(V.depthPacking)}function L(z,V){if(X.disableAll(),V.supportsVertexTextures)X.enable(0);if(V.instancing)X.enable(1);if(V.instancingColor)X.enable(2);if(V.instancingMorph)X.enable(3);if(V.matcap)X.enable(4);if(V.envMap)X.enable(5);if(V.normalMapObjectSpace)X.enable(6);if(V.normalMapTangentSpace)X.enable(7);if(V.clearcoat)X.enable(8);if(V.iridescence)X.enable(9);if(V.alphaTest)X.enable(10);if(V.vertexColors)X.enable(11);if(V.vertexAlphas)X.enable(12);if(V.vertexUv1s)X.enable(13);if(V.vertexUv2s)X.enable(14);if(V.vertexUv3s)X.enable(15);if(V.vertexTangents)X.enable(16);if(V.anisotropy)X.enable(17);if(V.alphaHash)X.enable(18);if(V.batching)X.enable(19);if(V.dispersion)X.enable(20);if(V.batchingColor)X.enable(21);if(V.gradientMap)X.enable(22);if(z.push(X.mask),X.disableAll(),V.fog)X.enable(0);if(V.useFog)X.enable(1);if(V.flatShading)X.enable(2);if(V.logarithmicDepthBuffer)X.enable(3);if(V.reversedDepthBuffer)X.enable(4);if(V.skinning)X.enable(5);if(V.morphTargets)X.enable(6);if(V.morphNormals)X.enable(7);if(V.morphColors)X.enable(8);if(V.premultipliedAlpha)X.enable(9);if(V.shadowMapEnabled)X.enable(10);if(V.doubleSided)X.enable(11);if(V.flipSided)X.enable(12);if(V.useDepthPacking)X.enable(13);if(V.dithering)X.enable(14);if(V.transmission)X.enable(15);if(V.sheen)X.enable(16);if(V.opaque)X.enable(17);if(V.pointsUvs)X.enable(18);if(V.decodeVideoTexture)X.enable(19);if(V.decodeVideoTextureEmissive)X.enable(20);if(V.alphaToCoverage)X.enable(21);z.push(X.mask)}function w(z){let V=k[z.type],j;if(V){let m=E8[V];j=mW.clone(m.uniforms)}else j=z.uniforms;return j}function v(z,V){let j;for(let m=0,l=G.length;m<l;m++){let c=G[m];if(c.cacheKey===V){j=c,++j.usedTimes;break}}if(j===void 0)j=new D1(J,V,z,H),G.push(j);return j}function _(z){if(--z.usedTimes===0){let V=G.indexOf(z);G[V]=G[G.length-1],G.pop(),z.destroy()}}function T(z){K.remove(z)}function x(){K.dispose()}return{getParameters:N,getProgramCacheKey:O,getUniforms:w,acquireProgram:v,releaseProgram:_,releaseShaderCache:T,programs:G,dispose:x}}function z1(){let J=new WeakMap;function Q(Y){return J.has(Y)}function $(Y){let X=J.get(Y);if(X===void 0)X={},J.set(Y,X);return X}function Z(Y){J.delete(Y)}function W(Y,X,K){J.get(Y)[X]=K}function H(){J=new WeakMap}return{has:Q,get:$,remove:Z,update:W,dispose:H}}function B1(J,Q){if(J.groupOrder!==Q.groupOrder)return J.groupOrder-Q.groupOrder;else if(J.renderOrder!==Q.renderOrder)return J.renderOrder-Q.renderOrder;else if(J.material.id!==Q.material.id)return J.material.id-Q.material.id;else if(J.z!==Q.z)return J.z-Q.z;else return J.id-Q.id}function kH(J,Q){if(J.groupOrder!==Q.groupOrder)return J.groupOrder-Q.groupOrder;else if(J.renderOrder!==Q.renderOrder)return J.renderOrder-Q.renderOrder;else if(J.z!==Q.z)return Q.z-J.z;else return J.id-Q.id}function MH(){let J=[],Q=0,$=[],Z=[],W=[];function H(){Q=0,$.length=0,Z.length=0,W.length=0}function Y(q,E,F,k,M,N){let O=J[Q];if(O===void 0)O={id:q.id,object:q,geometry:E,material:F,groupOrder:k,renderOrder:q.renderOrder,z:M,group:N},J[Q]=O;else O.id=q.id,O.object=q,O.geometry=E,O.material=F,O.groupOrder=k,O.renderOrder=q.renderOrder,O.z=M,O.group=N;return Q++,O}function X(q,E,F,k,M,N){let O=Y(q,E,F,k,M,N);if(F.transmission>0)Z.push(O);else if(F.transparent===!0)W.push(O);else $.push(O)}function K(q,E,F,k,M,N){let O=Y(q,E,F,k,M,N);if(F.transmission>0)Z.unshift(O);else if(F.transparent===!0)W.unshift(O);else $.unshift(O)}function U(q,E){if($.length>1)$.sort(q||B1);if(Z.length>1)Z.sort(E||kH);if(W.length>1)W.sort(E||kH)}function G(){for(let q=Q,E=J.length;q<E;q++){let F=J[q];if(F.id===null)break;F.id=null,F.object=null,F.geometry=null,F.material=null,F.group=null}}return{opaque:$,transmissive:Z,transparent:W,init:H,push:X,unshift:K,finish:G,sort:U}}function C1(){let J=new WeakMap;function Q(Z,W){let H=J.get(Z),Y;if(H===void 0)Y=new MH,J.set(Z,[Y]);else if(W>=H.length)Y=new MH,H.push(Y);else Y=H[W];return Y}function $(){J=new WeakMap}return{get:Q,dispose:$}}function w1(){let J={};return{get:function(Q){if(J[Q.id]!==void 0)return J[Q.id];let $;switch(Q.type){case"DirectionalLight":$={direction:new A,color:new jJ};break;case"SpotLight":$={position:new A,direction:new A,color:new jJ,distance:0,coneCos:0,penumbraCos:0,decay:0};break;case"PointLight":$={position:new A,color:new jJ,distance:0,decay:0};break;case"HemisphereLight":$={direction:new A,skyColor:new jJ,groundColor:new jJ};break;case"RectAreaLight":$={color:new jJ,position:new A,halfWidth:new A,halfHeight:new A};break}return J[Q.id]=$,$}}}function _1(){let J={};return{get:function(Q){if(J[Q.id]!==void 0)return J[Q.id];let $;switch(Q.type){case"DirectionalLight":$={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new PJ};break;case"SpotLight":$={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new PJ};break;case"PointLight":$={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new PJ,shadowCameraNear:1,shadowCameraFar:1000};break}return J[Q.id]=$,$}}}var I1=0;function P1(J,Q){return(Q.castShadow?2:0)-(J.castShadow?2:0)+(Q.map?1:0)-(J.map?1:0)}function T1(J){let Q=new w1,$=_1(),Z={version:0,hash:{directionalLength:-1,pointLength:-1,spotLength:-1,rectAreaLength:-1,hemiLength:-1,numDirectionalShadows:-1,numPointShadows:-1,numSpotShadows:-1,numSpotMaps:-1,numLightProbes:-1},ambient:[0,0,0],probe:[],directional:[],directionalShadow:[],directionalShadowMap:[],directionalShadowMatrix:[],spot:[],spotLightMap:[],spotShadow:[],spotShadowMap:[],spotLightMatrix:[],rectArea:[],rectAreaLTC1:null,rectAreaLTC2:null,point:[],pointShadow:[],pointShadowMap:[],pointShadowMatrix:[],hemi:[],numSpotLightShadowsWithMaps:0,numLightProbes:0};for(let U=0;U<9;U++)Z.probe.push(new A);let W=new A,H=new vJ,Y=new vJ;function X(U){let G=0,q=0,E=0;for(let z=0;z<9;z++)Z.probe[z].set(0,0,0);let F=0,k=0,M=0,N=0,O=0,C=0,L=0,w=0,v=0,_=0,T=0;U.sort(P1);for(let z=0,V=U.length;z<V;z++){let j=U[z],m=j.color,l=j.intensity,c=j.distance,i=j.shadow&&j.shadow.map?j.shadow.map.texture:null;if(j.isAmbientLight)G+=m.r*l,q+=m.g*l,E+=m.b*l;else if(j.isLightProbe){for(let u=0;u<9;u++)Z.probe[u].addScaledVector(j.sh.coefficients[u],l);T++}else if(j.isDirectionalLight){let u=Q.get(j);if(u.color.copy(j.color).multiplyScalar(j.intensity),j.castShadow){let r=j.shadow,g=$.get(j);g.shadowIntensity=r.intensity,g.shadowBias=r.bias,g.shadowNormalBias=r.normalBias,g.shadowRadius=r.radius,g.shadowMapSize=r.mapSize,Z.directionalShadow[F]=g,Z.directionalShadowMap[F]=i,Z.directionalShadowMatrix[F]=j.shadow.matrix,C++}Z.directional[F]=u,F++}else if(j.isSpotLight){let u=Q.get(j);u.position.setFromMatrixPosition(j.matrixWorld),u.color.copy(m).multiplyScalar(l),u.distance=c,u.coneCos=Math.cos(j.angle),u.penumbraCos=Math.cos(j.angle*(1-j.penumbra)),u.decay=j.decay,Z.spot[M]=u;let r=j.shadow;if(j.map){if(Z.spotLightMap[v]=j.map,v++,r.updateMatrices(j),j.castShadow)_++}if(Z.spotLightMatrix[M]=r.matrix,j.castShadow){let g=$.get(j);g.shadowIntensity=r.intensity,g.shadowBias=r.bias,g.shadowNormalBias=r.normalBias,g.shadowRadius=r.radius,g.shadowMapSize=r.mapSize,Z.spotShadow[M]=g,Z.spotShadowMap[M]=i,w++}M++}else if(j.isRectAreaLight){let u=Q.get(j);u.color.copy(m).multiplyScalar(l),u.halfWidth.set(j.width*0.5,0,0),u.halfHeight.set(0,j.height*0.5,0),Z.rectArea[N]=u,N++}else if(j.isPointLight){let u=Q.get(j);if(u.color.copy(j.color).multiplyScalar(j.intensity),u.distance=j.distance,u.decay=j.decay,j.castShadow){let r=j.shadow,g=$.get(j);g.shadowIntensity=r.intensity,g.shadowBias=r.bias,g.shadowNormalBias=r.normalBias,g.shadowRadius=r.radius,g.shadowMapSize=r.mapSize,g.shadowCameraNear=r.camera.near,g.shadowCameraFar=r.camera.far,Z.pointShadow[k]=g,Z.pointShadowMap[k]=i,Z.pointShadowMatrix[k]=j.shadow.matrix,L++}Z.point[k]=u,k++}else if(j.isHemisphereLight){let u=Q.get(j);u.skyColor.copy(j.color).multiplyScalar(l),u.groundColor.copy(j.groundColor).multiplyScalar(l),Z.hemi[O]=u,O++}}if(N>0)if(J.has("OES_texture_float_linear")===!0)Z.rectAreaLTC1=$J.LTC_FLOAT_1,Z.rectAreaLTC2=$J.LTC_FLOAT_2;else Z.rectAreaLTC1=$J.LTC_HALF_1,Z.rectAreaLTC2=$J.LTC_HALF_2;Z.ambient[0]=G,Z.ambient[1]=q,Z.ambient[2]=E;let x=Z.hash;if(x.directionalLength!==F||x.pointLength!==k||x.spotLength!==M||x.rectAreaLength!==N||x.hemiLength!==O||x.numDirectionalShadows!==C||x.numPointShadows!==L||x.numSpotShadows!==w||x.numSpotMaps!==v||x.numLightProbes!==T)Z.directional.length=F,Z.spot.length=M,Z.rectArea.length=N,Z.point.length=k,Z.hemi.length=O,Z.directionalShadow.length=C,Z.directionalShadowMap.length=C,Z.pointShadow.length=L,Z.pointShadowMap.length=L,Z.spotShadow.length=w,Z.spotShadowMap.length=w,Z.directionalShadowMatrix.length=C,Z.pointShadowMatrix.length=L,Z.spotLightMatrix.length=w+v-_,Z.spotLightMap.length=v,Z.numSpotLightShadowsWithMaps=_,Z.numLightProbes=T,x.directionalLength=F,x.pointLength=k,x.spotLength=M,x.rectAreaLength=N,x.hemiLength=O,x.numDirectionalShadows=C,x.numPointShadows=L,x.numSpotShadows=w,x.numSpotMaps=v,x.numLightProbes=T,Z.version=I1++}function K(U,G){let q=0,E=0,F=0,k=0,M=0,N=G.matrixWorldInverse;for(let O=0,C=U.length;O<C;O++){let L=U[O];if(L.isDirectionalLight){let w=Z.directional[q];w.direction.setFromMatrixPosition(L.matrixWorld),W.setFromMatrixPosition(L.target.matrixWorld),w.direction.sub(W),w.direction.transformDirection(N),q++}else if(L.isSpotLight){let w=Z.spot[F];w.position.setFromMatrixPosition(L.matrixWorld),w.position.applyMatrix4(N),w.direction.setFromMatrixPosition(L.matrixWorld),W.setFromMatrixPosition(L.target.matrixWorld),w.direction.sub(W),w.direction.transformDirection(N),F++}else if(L.isRectAreaLight){let w=Z.rectArea[k];w.position.setFromMatrixPosition(L.matrixWorld),w.position.applyMatrix4(N),Y.identity(),H.copy(L.matrixWorld),H.premultiply(N),Y.extractRotation(H),w.halfWidth.set(L.width*0.5,0,0),w.halfHeight.set(0,L.height*0.5,0),w.halfWidth.applyMatrix4(Y),w.halfHeight.applyMatrix4(Y),k++}else if(L.isPointLight){let w=Z.point[E];w.position.setFromMatrixPosition(L.matrixWorld),w.position.applyMatrix4(N),E++}else if(L.isHemisphereLight){let w=Z.hemi[M];w.direction.setFromMatrixPosition(L.matrixWorld),w.direction.transformDirection(N),M++}}}return{setup:X,setupView:K,state:Z}}function DH(J){let Q=new T1(J),$=[],Z=[];function W(G){U.camera=G,$.length=0,Z.length=0}function H(G){$.push(G)}function Y(G){Z.push(G)}function X(){Q.setup($)}function K(G){Q.setupView($,G)}let U={lightsArray:$,shadowsArray:Z,camera:null,lights:Q,transmissionRenderTarget:{}};return{init:W,state:U,setupLights:X,setupLightsView:K,pushLight:H,pushShadow:Y}}function A1(J){let Q=new WeakMap;function $(W,H=0){let Y=Q.get(W),X;if(Y===void 0)X=new DH(J),Q.set(W,[X]);else if(H>=Y.length)X=new DH(J),Y.push(X);else X=Y[H];return X}function Z(){Q=new WeakMap}return{get:$,dispose:Z}}var S1=`void main() {
	gl_Position = vec4( position, 1.0 );
}`,j1=`uniform sampler2D shadow_pass;
uniform vec2 resolution;
uniform float radius;
#include <packing>
void main() {
	const float samples = float( VSM_SAMPLES );
	float mean = 0.0;
	float squared_mean = 0.0;
	float uvStride = samples <= 1.0 ? 0.0 : 2.0 / ( samples - 1.0 );
	float uvStart = samples <= 1.0 ? 0.0 : - 1.0;
	for ( float i = 0.0; i < samples; i ++ ) {
		float uvOffset = uvStart + i * uvStride;
		#ifdef HORIZONTAL_PASS
			vec2 distribution = unpackRGBATo2Half( texture2D( shadow_pass, ( gl_FragCoord.xy + vec2( uvOffset, 0.0 ) * radius ) / resolution ) );
			mean += distribution.x;
			squared_mean += distribution.y * distribution.y + distribution.x * distribution.x;
		#else
			float depth = unpackRGBAToDepth( texture2D( shadow_pass, ( gl_FragCoord.xy + vec2( 0.0, uvOffset ) * radius ) / resolution ) );
			mean += depth;
			squared_mean += depth * depth;
		#endif
	}
	mean = mean / samples;
	squared_mean = squared_mean / samples;
	float std_dev = sqrt( squared_mean - mean * mean );
	gl_FragColor = pack2HalfToRGBA( vec2( mean, std_dev ) );
}`;function y1(J,Q,$){let Z=new M6,W=new PJ,H=new PJ,Y=new sJ,X=new V$({depthPacking:AW}),K=new z$,U={},G=$.maxTextureSize,q={[x8]:b0,[b0]:x8,[o0]:o0},E=new q8({defines:{VSM_SAMPLES:8},uniforms:{shadow_pass:{value:null},resolution:{value:new PJ},radius:{value:4}},vertexShader:S1,fragmentShader:j1}),F=E.clone();F.defines.HORIZONTAL_PASS=1;let k=new p0;k.setAttribute("position",new F0(new Float32Array([-1,-1,0.5,3,-1,0.5,-1,3,0.5]),3));let M=new C0(k,E),N=this;this.enabled=!1,this.autoUpdate=!0,this.needsUpdate=!1,this.type=wQ;let O=this.type;this.render=function(_,T,x){if(N.enabled===!1)return;if(N.autoUpdate===!1&&N.needsUpdate===!1)return;if(_.length===0)return;let z=J.getRenderTarget(),V=J.getActiveCubeFace(),j=J.getActiveMipmapLevel(),m=J.state;if(m.setBlending(g8),m.buffers.depth.getReversed())m.buffers.color.setClear(0,0,0,0);else m.buffers.color.setClear(1,1,1,1);m.buffers.depth.setTest(!0),m.setScissorTest(!1);let l=O!==K8&&this.type===K8,c=O===K8&&this.type!==K8;for(let i=0,u=_.length;i<u;i++){let r=_[i],g=r.shadow;if(g===void 0){console.warn("THREE.WebGLShadowMap:",r,"has no shadow.");continue}if(g.autoUpdate===!1&&g.needsUpdate===!1)continue;W.copy(g.mapSize);let ZJ=g.getFrameExtents();if(W.multiply(ZJ),H.copy(g.mapSize),W.x>G||W.y>G){if(W.x>G)H.x=Math.floor(G/ZJ.x),W.x=H.x*ZJ.x,g.mapSize.x=H.x;if(W.y>G)H.y=Math.floor(G/ZJ.y),W.y=H.y*ZJ.y,g.mapSize.y=H.y}if(g.map===null||l===!0||c===!0){let TJ=this.type!==K8?{minFilter:B8,magFilter:B8}:{};if(g.map!==null)g.map.dispose();g.map=new _8(W.x,W.y,TJ),g.map.texture.name=r.name+".shadowMap",g.camera.updateProjectionMatrix()}J.setRenderTarget(g.map),J.clear();let UJ=g.getViewportCount();for(let TJ=0;TJ<UJ;TJ++){let mJ=g.getViewport(TJ);Y.set(H.x*mJ.x,H.y*mJ.y,H.x*mJ.z,H.y*mJ.w),m.viewport(Y),g.updateMatrices(r,TJ),Z=g.getFrustum(),w(T,x,g.camera,r,this.type)}if(g.isPointLightShadow!==!0&&this.type===K8)C(g,x);g.needsUpdate=!1}O=this.type,N.needsUpdate=!1,J.setRenderTarget(z,V,j)};function C(_,T){let x=Q.update(M);if(E.defines.VSM_SAMPLES!==_.blurSamples)E.defines.VSM_SAMPLES=_.blurSamples,F.defines.VSM_SAMPLES=_.blurSamples,E.needsUpdate=!0,F.needsUpdate=!0;if(_.mapPass===null)_.mapPass=new _8(W.x,W.y);E.uniforms.shadow_pass.value=_.map.texture,E.uniforms.resolution.value=_.mapSize,E.uniforms.radius.value=_.radius,J.setRenderTarget(_.mapPass),J.clear(),J.renderBufferDirect(T,null,x,E,M,null),F.uniforms.shadow_pass.value=_.mapPass.texture,F.uniforms.resolution.value=_.mapSize,F.uniforms.radius.value=_.radius,J.setRenderTarget(_.map),J.clear(),J.renderBufferDirect(T,null,x,F,M,null)}function L(_,T,x,z){let V=null,j=x.isPointLight===!0?_.customDistanceMaterial:_.customDepthMaterial;if(j!==void 0)V=j;else if(V=x.isPointLight===!0?K:X,J.localClippingEnabled&&T.clipShadows===!0&&Array.isArray(T.clippingPlanes)&&T.clippingPlanes.length!==0||T.displacementMap&&T.displacementScale!==0||T.alphaMap&&T.alphaTest>0||T.map&&T.alphaTest>0||T.alphaToCoverage===!0){let m=V.uuid,l=T.uuid,c=U[m];if(c===void 0)c={},U[m]=c;let i=c[l];if(i===void 0)i=V.clone(),c[l]=i,T.addEventListener("dispose",v);V=i}if(V.visible=T.visible,V.wireframe=T.wireframe,z===K8)V.side=T.shadowSide!==null?T.shadowSide:T.side;else V.side=T.shadowSide!==null?T.shadowSide:q[T.side];if(V.alphaMap=T.alphaMap,V.alphaTest=T.alphaToCoverage===!0?0.5:T.alphaTest,V.map=T.map,V.clipShadows=T.clipShadows,V.clippingPlanes=T.clippingPlanes,V.clipIntersection=T.clipIntersection,V.displacementMap=T.displacementMap,V.displacementScale=T.displacementScale,V.displacementBias=T.displacementBias,V.wireframeLinewidth=T.wireframeLinewidth,V.linewidth=T.linewidth,x.isPointLight===!0&&V.isMeshDistanceMaterial===!0){let m=J.properties.get(V);m.light=x}return V}function w(_,T,x,z,V){if(_.visible===!1)return;if(_.layers.test(T.layers)&&(_.isMesh||_.isLine||_.isPoints)){if((_.castShadow||_.receiveShadow&&V===K8)&&(!_.frustumCulled||Z.intersectsObject(_))){_.modelViewMatrix.multiplyMatrices(x.matrixWorldInverse,_.matrixWorld);let l=Q.update(_),c=_.material;if(Array.isArray(c)){let i=l.groups;for(let u=0,r=i.length;u<r;u++){let g=i[u],ZJ=c[g.materialIndex];if(ZJ&&ZJ.visible){let UJ=L(_,ZJ,z,V);_.onBeforeShadow(J,_,T,x,l,UJ,g),J.renderBufferDirect(x,null,l,UJ,_,g),_.onAfterShadow(J,_,T,x,l,UJ,g)}}}else if(c.visible){let i=L(_,c,z,V);_.onBeforeShadow(J,_,T,x,l,i,null),J.renderBufferDirect(x,null,l,i,_,null),_.onAfterShadow(J,_,T,x,l,i,null)}}}let m=_.children;for(let l=0,c=m.length;l<c;l++)w(m[l],T,x,z,V)}function v(_){_.target.removeEventListener("dispose",v);for(let x in U){let z=U[x],V=_.target.uuid;if(V in z)z[V].dispose(),delete z[V]}}}var v1={[Q7]:$7,[Z7]:Y7,[W7]:X7,[X6]:H7,[$7]:Q7,[Y7]:Z7,[X7]:W7,[H7]:X6};function f1(J,Q){function $(){let P=!1,HJ=new sJ,QJ=null,NJ=new sJ(0,0,0,0);return{setMask:function(a){if(QJ!==a&&!P)J.colorMask(a,a,a,a),QJ=a},setLocked:function(a){P=a},setClear:function(a,s,FJ,yJ,J0){if(J0===!0)a*=yJ,s*=yJ,FJ*=yJ;if(HJ.set(a,s,FJ,yJ),NJ.equals(HJ)===!1)J.clearColor(a,s,FJ,yJ),NJ.copy(HJ)},reset:function(){P=!1,QJ=null,NJ.set(-1,0,0,0)}}}function Z(){let P=!1,HJ=!1,QJ=null,NJ=null,a=null;return{setReversed:function(s){if(HJ!==s){let FJ=Q.get("EXT_clip_control");if(s)FJ.clipControlEXT(FJ.LOWER_LEFT_EXT,FJ.ZERO_TO_ONE_EXT);else FJ.clipControlEXT(FJ.LOWER_LEFT_EXT,FJ.NEGATIVE_ONE_TO_ONE_EXT);HJ=s;let yJ=a;a=null,this.setClear(yJ)}},getReversed:function(){return HJ},setTest:function(s){if(s)GJ(J.DEPTH_TEST);else RJ(J.DEPTH_TEST)},setMask:function(s){if(QJ!==s&&!P)J.depthMask(s),QJ=s},setFunc:function(s){if(HJ)s=v1[s];if(NJ!==s){switch(s){case Q7:J.depthFunc(J.NEVER);break;case $7:J.depthFunc(J.ALWAYS);break;case Z7:J.depthFunc(J.LESS);break;case X6:J.depthFunc(J.LEQUAL);break;case W7:J.depthFunc(J.EQUAL);break;case H7:J.depthFunc(J.GEQUAL);break;case Y7:J.depthFunc(J.GREATER);break;case X7:J.depthFunc(J.NOTEQUAL);break;default:J.depthFunc(J.LEQUAL)}NJ=s}},setLocked:function(s){P=s},setClear:function(s){if(a!==s){if(HJ)s=1-s;J.clearDepth(s),a=s}},reset:function(){P=!1,QJ=null,NJ=null,a=null,HJ=!1}}}function W(){let P=!1,HJ=null,QJ=null,NJ=null,a=null,s=null,FJ=null,yJ=null,J0=null;return{setTest:function(rJ){if(!P)if(rJ)GJ(J.STENCIL_TEST);else RJ(J.STENCIL_TEST)},setMask:function(rJ){if(HJ!==rJ&&!P)J.stencilMask(rJ),HJ=rJ},setFunc:function(rJ,W8,H8){if(QJ!==rJ||NJ!==W8||a!==H8)J.stencilFunc(rJ,W8,H8),QJ=rJ,NJ=W8,a=H8},setOp:function(rJ,W8,H8){if(s!==rJ||FJ!==W8||yJ!==H8)J.stencilOp(rJ,W8,H8),s=rJ,FJ=W8,yJ=H8},setLocked:function(rJ){P=rJ},setClear:function(rJ){if(J0!==rJ)J.clearStencil(rJ),J0=rJ},reset:function(){P=!1,HJ=null,QJ=null,NJ=null,a=null,s=null,FJ=null,yJ=null,J0=null}}}let H=new $,Y=new Z,X=new W,K=new WeakMap,U=new WeakMap,G={},q={},E=new WeakMap,F=[],k=null,M=!1,N=null,O=null,C=null,L=null,w=null,v=null,_=null,T=new jJ(0,0,0),x=0,z=!1,V=null,j=null,m=null,l=null,c=null,i=J.getParameter(J.MAX_COMBINED_TEXTURE_IMAGE_UNITS),u=!1,r=0,g=J.getParameter(J.VERSION);if(g.indexOf("WebGL")!==-1)r=parseFloat(/^WebGL (\d)/.exec(g)[1]),u=r>=1;else if(g.indexOf("OpenGL ES")!==-1)r=parseFloat(/^OpenGL ES (\d)/.exec(g)[1]),u=r>=2;let ZJ=null,UJ={},TJ=J.getParameter(J.SCISSOR_BOX),mJ=J.getParameter(J.VIEWPORT),Y0=new sJ().fromArray(TJ),d=new sJ().fromArray(mJ);function WJ(P,HJ,QJ,NJ){let a=new Uint8Array(4),s=J.createTexture();J.bindTexture(P,s),J.texParameteri(P,J.TEXTURE_MIN_FILTER,J.NEAREST),J.texParameteri(P,J.TEXTURE_MAG_FILTER,J.NEAREST);for(let FJ=0;FJ<QJ;FJ++)if(P===J.TEXTURE_3D||P===J.TEXTURE_2D_ARRAY)J.texImage3D(HJ,0,J.RGBA,1,1,NJ,0,J.RGBA,J.UNSIGNED_BYTE,a);else J.texImage2D(HJ+FJ,0,J.RGBA,1,1,0,J.RGBA,J.UNSIGNED_BYTE,a);return s}let MJ={};MJ[J.TEXTURE_2D]=WJ(J.TEXTURE_2D,J.TEXTURE_2D,1),MJ[J.TEXTURE_CUBE_MAP]=WJ(J.TEXTURE_CUBE_MAP,J.TEXTURE_CUBE_MAP_POSITIVE_X,6),MJ[J.TEXTURE_2D_ARRAY]=WJ(J.TEXTURE_2D_ARRAY,J.TEXTURE_2D_ARRAY,1,1),MJ[J.TEXTURE_3D]=WJ(J.TEXTURE_3D,J.TEXTURE_3D,1,1),H.setClear(0,0,0,1),Y.setClear(1),X.setClear(0),GJ(J.DEPTH_TEST),Y.setFunc(X6),zJ(!1),X0(CQ),GJ(J.CULL_FACE),CJ(g8);function GJ(P){if(G[P]!==!0)J.enable(P),G[P]=!0}function RJ(P){if(G[P]!==!1)J.disable(P),G[P]=!1}function uJ(P,HJ){if(q[P]!==HJ){if(J.bindFramebuffer(P,HJ),q[P]=HJ,P===J.DRAW_FRAMEBUFFER)q[J.FRAMEBUFFER]=HJ;if(P===J.FRAMEBUFFER)q[J.DRAW_FRAMEBUFFER]=HJ;return!0}return!1}function cJ(P,HJ){let QJ=F,NJ=!1;if(P){if(QJ=E.get(HJ),QJ===void 0)QJ=[],E.set(HJ,QJ);let a=P.textures;if(QJ.length!==a.length||QJ[0]!==J.COLOR_ATTACHMENT0){for(let s=0,FJ=a.length;s<FJ;s++)QJ[s]=J.COLOR_ATTACHMENT0+s;QJ.length=a.length,NJ=!0}}else if(QJ[0]!==J.BACK)QJ[0]=J.BACK,NJ=!0;if(NJ)J.drawBuffers(QJ)}function dJ(P){if(k!==P)return J.useProgram(P),k=P,!0;return!1}let I={[S9]:J.FUNC_ADD,[sZ]:J.FUNC_SUBTRACT,[oZ]:J.FUNC_REVERSE_SUBTRACT};I[iZ]=J.MIN,I[aZ]=J.MAX;let $0={[rZ]:J.ZERO,[tZ]:J.ONE,[eZ]:J.SRC_COLOR,[QW]:J.SRC_ALPHA,[XW]:J.SRC_ALPHA_SATURATE,[HW]:J.DST_COLOR,[ZW]:J.DST_ALPHA,[JW]:J.ONE_MINUS_SRC_COLOR,[$W]:J.ONE_MINUS_SRC_ALPHA,[YW]:J.ONE_MINUS_DST_COLOR,[WW]:J.ONE_MINUS_DST_ALPHA,[KW]:J.CONSTANT_COLOR,[UW]:J.ONE_MINUS_CONSTANT_COLOR,[GW]:J.CONSTANT_ALPHA,[qW]:J.ONE_MINUS_CONSTANT_ALPHA};function CJ(P,HJ,QJ,NJ,a,s,FJ,yJ,J0,rJ){if(P===g8){if(M===!0)RJ(J.BLEND),M=!1;return}if(M===!1)GJ(J.BLEND),M=!0;if(P!==nZ){if(P!==N||rJ!==z){if(O!==S9||w!==S9)J.blendEquation(J.FUNC_ADD),O=S9,w=S9;if(rJ)switch(P){case Y6:J.blendFuncSeparate(J.ONE,J.ONE_MINUS_SRC_ALPHA,J.ONE,J.ONE_MINUS_SRC_ALPHA);break;case _Q:J.blendFunc(J.ONE,J.ONE);break;case IQ:J.blendFuncSeparate(J.ZERO,J.ONE_MINUS_SRC_COLOR,J.ZERO,J.ONE);break;case PQ:J.blendFuncSeparate(J.DST_COLOR,J.ONE_MINUS_SRC_ALPHA,J.ZERO,J.ONE);break;default:console.error("THREE.WebGLState: Invalid blending: ",P);break}else switch(P){case Y6:J.blendFuncSeparate(J.SRC_ALPHA,J.ONE_MINUS_SRC_ALPHA,J.ONE,J.ONE_MINUS_SRC_ALPHA);break;case _Q:J.blendFuncSeparate(J.SRC_ALPHA,J.ONE,J.ONE,J.ONE);break;case IQ:console.error("THREE.WebGLState: SubtractiveBlending requires material.premultipliedAlpha = true");break;case PQ:console.error("THREE.WebGLState: MultiplyBlending requires material.premultipliedAlpha = true");break;default:console.error("THREE.WebGLState: Invalid blending: ",P);break}C=null,L=null,v=null,_=null,T.set(0,0,0),x=0,N=P,z=rJ}return}if(a=a||HJ,s=s||QJ,FJ=FJ||NJ,HJ!==O||a!==w)J.blendEquationSeparate(I[HJ],I[a]),O=HJ,w=a;if(QJ!==C||NJ!==L||s!==v||FJ!==_)J.blendFuncSeparate($0[QJ],$0[NJ],$0[s],$0[FJ]),C=QJ,L=NJ,v=s,_=FJ;if(yJ.equals(T)===!1||J0!==x)J.blendColor(yJ.r,yJ.g,yJ.b,J0),T.copy(yJ),x=J0;N=P,z=!1}function iJ(P,HJ){P.side===o0?RJ(J.CULL_FACE):GJ(J.CULL_FACE);let QJ=P.side===b0;if(HJ)QJ=!QJ;zJ(QJ),P.blending===Y6&&P.transparent===!1?CJ(g8):CJ(P.blending,P.blendEquation,P.blendSrc,P.blendDst,P.blendEquationAlpha,P.blendSrcAlpha,P.blendDstAlpha,P.blendColor,P.blendAlpha,P.premultipliedAlpha),Y.setFunc(P.depthFunc),Y.setTest(P.depthTest),Y.setMask(P.depthWrite),H.setMask(P.colorWrite);let NJ=P.stencilWrite;if(X.setTest(NJ),NJ)X.setMask(P.stencilWriteMask),X.setFunc(P.stencilFunc,P.stencilRef,P.stencilFuncMask),X.setOp(P.stencilFail,P.stencilZFail,P.stencilZPass);_J(P.polygonOffset,P.polygonOffsetFactor,P.polygonOffsetUnits),P.alphaToCoverage===!0?GJ(J.SAMPLE_ALPHA_TO_COVERAGE):RJ(J.SAMPLE_ALPHA_TO_COVERAGE)}function zJ(P){if(V!==P){if(P)J.frontFace(J.CW);else J.frontFace(J.CCW);V=P}}function X0(P){if(P!==mZ){if(GJ(J.CULL_FACE),P!==j)if(P===CQ)J.cullFace(J.BACK);else if(P===uZ)J.cullFace(J.FRONT);else J.cullFace(J.FRONT_AND_BACK)}else RJ(J.CULL_FACE);j=P}function DJ(P){if(P!==m){if(u)J.lineWidth(P);m=P}}function _J(P,HJ,QJ){if(P){if(GJ(J.POLYGON_OFFSET_FILL),l!==HJ||c!==QJ)J.polygonOffset(HJ,QJ),l=HJ,c=QJ}else RJ(J.POLYGON_OFFSET_FILL)}function V0(P){if(P)GJ(J.SCISSOR_TEST);else RJ(J.SCISSOR_TEST)}function D0(P){if(P===void 0)P=J.TEXTURE0+i-1;if(ZJ!==P)J.activeTexture(P),ZJ=P}function N0(P,HJ,QJ){if(QJ===void 0)if(ZJ===null)QJ=J.TEXTURE0+i-1;else QJ=ZJ;let NJ=UJ[QJ];if(NJ===void 0)NJ={type:void 0,texture:void 0},UJ[QJ]=NJ;if(NJ.type!==P||NJ.texture!==HJ){if(ZJ!==QJ)J.activeTexture(QJ),ZJ=QJ;J.bindTexture(P,HJ||MJ[P]),NJ.type=P,NJ.texture=HJ}}function B(){let P=UJ[ZJ];if(P!==void 0&&P.type!==void 0)J.bindTexture(P.type,null),P.type=void 0,P.texture=void 0}function R(){try{J.compressedTexImage2D(...arguments)}catch(P){console.error("THREE.WebGLState:",P)}}function f(){try{J.compressedTexImage3D(...arguments)}catch(P){console.error("THREE.WebGLState:",P)}}function n(){try{J.texSubImage2D(...arguments)}catch(P){console.error("THREE.WebGLState:",P)}}function o(){try{J.texSubImage3D(...arguments)}catch(P){console.error("THREE.WebGLState:",P)}}function p(){try{J.compressedTexSubImage2D(...arguments)}catch(P){console.error("THREE.WebGLState:",P)}}function EJ(){try{J.compressedTexSubImage3D(...arguments)}catch(P){console.error("THREE.WebGLState:",P)}}function JJ(){try{J.texStorage2D(...arguments)}catch(P){console.error("THREE.WebGLState:",P)}}function kJ(){try{J.texStorage3D(...arguments)}catch(P){console.error("THREE.WebGLState:",P)}}function AJ(){try{J.texImage2D(...arguments)}catch(P){console.error("THREE.WebGLState:",P)}}function e(){try{J.texImage3D(...arguments)}catch(P){console.error("THREE.WebGLState:",P)}}function XJ(P){if(Y0.equals(P)===!1)J.scissor(P.x,P.y,P.z,P.w),Y0.copy(P)}function LJ(P){if(d.equals(P)===!1)J.viewport(P.x,P.y,P.z,P.w),d.copy(P)}function VJ(P,HJ){let QJ=U.get(HJ);if(QJ===void 0)QJ=new WeakMap,U.set(HJ,QJ);let NJ=QJ.get(P);if(NJ===void 0)NJ=J.getUniformBlockIndex(HJ,P.name),QJ.set(P,NJ)}function KJ(P,HJ){let NJ=U.get(HJ).get(P);if(K.get(HJ)!==NJ)J.uniformBlockBinding(HJ,NJ,P.__bindingPointIndex),K.set(HJ,NJ)}function bJ(){J.disable(J.BLEND),J.disable(J.CULL_FACE),J.disable(J.DEPTH_TEST),J.disable(J.POLYGON_OFFSET_FILL),J.disable(J.SCISSOR_TEST),J.disable(J.STENCIL_TEST),J.disable(J.SAMPLE_ALPHA_TO_COVERAGE),J.blendEquation(J.FUNC_ADD),J.blendFunc(J.ONE,J.ZERO),J.blendFuncSeparate(J.ONE,J.ZERO,J.ONE,J.ZERO),J.blendColor(0,0,0,0),J.colorMask(!0,!0,!0,!0),J.clearColor(0,0,0,0),J.depthMask(!0),J.depthFunc(J.LESS),Y.setReversed(!1),J.clearDepth(1),J.stencilMask(4294967295),J.stencilFunc(J.ALWAYS,0,4294967295),J.stencilOp(J.KEEP,J.KEEP,J.KEEP),J.clearStencil(0),J.cullFace(J.BACK),J.frontFace(J.CCW),J.polygonOffset(0,0),J.activeTexture(J.TEXTURE0),J.bindFramebuffer(J.FRAMEBUFFER,null),J.bindFramebuffer(J.DRAW_FRAMEBUFFER,null),J.bindFramebuffer(J.READ_FRAMEBUFFER,null),J.useProgram(null),J.lineWidth(1),J.scissor(0,0,J.canvas.width,J.canvas.height),J.viewport(0,0,J.canvas.width,J.canvas.height),G={},ZJ=null,UJ={},q={},E=new WeakMap,F=[],k=null,M=!1,N=null,O=null,C=null,L=null,w=null,v=null,_=null,T=new jJ(0,0,0),x=0,z=!1,V=null,j=null,m=null,l=null,c=null,Y0.set(0,0,J.canvas.width,J.canvas.height),d.set(0,0,J.canvas.width,J.canvas.height),H.reset(),Y.reset(),X.reset()}return{buffers:{color:H,depth:Y,stencil:X},enable:GJ,disable:RJ,bindFramebuffer:uJ,drawBuffers:cJ,useProgram:dJ,setBlending:CJ,setMaterial:iJ,setFlipSided:zJ,setCullFace:X0,setLineWidth:DJ,setPolygonOffset:_J,setScissorTest:V0,activeTexture:D0,bindTexture:N0,unbindTexture:B,compressedTexImage2D:R,compressedTexImage3D:f,texImage2D:AJ,texImage3D:e,updateUBOMapping:VJ,uniformBlockBinding:KJ,texStorage2D:JJ,texStorage3D:kJ,texSubImage2D:n,texSubImage3D:o,compressedTexSubImage2D:p,compressedTexSubImage3D:EJ,scissor:XJ,viewport:LJ,reset:bJ}}function h1(J,Q,$,Z,W,H,Y){let X=Q.has("WEBGL_multisampled_render_to_texture")?Q.get("WEBGL_multisampled_render_to_texture"):null,K=typeof navigator==="undefined"?!1:/OculusBrowser/g.test(navigator.userAgent),U=new PJ,G=new WeakMap,q,E=new WeakMap,F=!1;try{F=typeof OffscreenCanvas!=="undefined"&&new OffscreenCanvas(1,1).getContext("2d")!==null}catch(B){}function k(B,R){return F?new OffscreenCanvas(B,R):A9("canvas")}function M(B,R,f){let n=1,o=N0(B);if(o.width>f||o.height>f)n=f/Math.max(o.width,o.height);if(n<1)if(typeof HTMLImageElement!=="undefined"&&B instanceof HTMLImageElement||typeof HTMLCanvasElement!=="undefined"&&B instanceof HTMLCanvasElement||typeof ImageBitmap!=="undefined"&&B instanceof ImageBitmap||typeof VideoFrame!=="undefined"&&B instanceof VideoFrame){let p=Math.floor(n*o.width),EJ=Math.floor(n*o.height);if(q===void 0)q=k(p,EJ);let JJ=R?k(p,EJ):q;return JJ.width=p,JJ.height=EJ,JJ.getContext("2d").drawImage(B,0,0,p,EJ),console.warn("THREE.WebGLRenderer: Texture has been resized from ("+o.width+"x"+o.height+") to ("+p+"x"+EJ+")."),JJ}else{if("data"in B)console.warn("THREE.WebGLRenderer: Image in DataTexture is too big ("+o.width+"x"+o.height+").");return B}return B}function N(B){return B.generateMipmaps}function O(B){J.generateMipmap(B)}function C(B){if(B.isWebGLCubeRenderTarget)return J.TEXTURE_CUBE_MAP;if(B.isWebGL3DRenderTarget)return J.TEXTURE_3D;if(B.isWebGLArrayRenderTarget||B.isCompressedArrayTexture)return J.TEXTURE_2D_ARRAY;return J.TEXTURE_2D}function L(B,R,f,n,o=!1){if(B!==null){if(J[B]!==void 0)return J[B];console.warn("THREE.WebGLRenderer: Attempt to use non-existing WebGL internal format '"+B+"'")}let p=R;if(R===J.RED){if(f===J.FLOAT)p=J.R32F;if(f===J.HALF_FLOAT)p=J.R16F;if(f===J.UNSIGNED_BYTE)p=J.R8}if(R===J.RED_INTEGER){if(f===J.UNSIGNED_BYTE)p=J.R8UI;if(f===J.UNSIGNED_SHORT)p=J.R16UI;if(f===J.UNSIGNED_INT)p=J.R32UI;if(f===J.BYTE)p=J.R8I;if(f===J.SHORT)p=J.R16I;if(f===J.INT)p=J.R32I}if(R===J.RG){if(f===J.FLOAT)p=J.RG32F;if(f===J.HALF_FLOAT)p=J.RG16F;if(f===J.UNSIGNED_BYTE)p=J.RG8}if(R===J.RG_INTEGER){if(f===J.UNSIGNED_BYTE)p=J.RG8UI;if(f===J.UNSIGNED_SHORT)p=J.RG16UI;if(f===J.UNSIGNED_INT)p=J.RG32UI;if(f===J.BYTE)p=J.RG8I;if(f===J.SHORT)p=J.RG16I;if(f===J.INT)p=J.RG32I}if(R===J.RGB_INTEGER){if(f===J.UNSIGNED_BYTE)p=J.RGB8UI;if(f===J.UNSIGNED_SHORT)p=J.RGB16UI;if(f===J.UNSIGNED_INT)p=J.RGB32UI;if(f===J.BYTE)p=J.RGB8I;if(f===J.SHORT)p=J.RGB16I;if(f===J.INT)p=J.RGB32I}if(R===J.RGBA_INTEGER){if(f===J.UNSIGNED_BYTE)p=J.RGBA8UI;if(f===J.UNSIGNED_SHORT)p=J.RGBA16UI;if(f===J.UNSIGNED_INT)p=J.RGBA32UI;if(f===J.BYTE)p=J.RGBA8I;if(f===J.SHORT)p=J.RGBA16I;if(f===J.INT)p=J.RGBA32I}if(R===J.RGB){if(f===J.UNSIGNED_INT_5_9_9_9_REV)p=J.RGB9_E5}if(R===J.RGBA){let EJ=o?U$:lJ.getTransfer(n);if(f===J.FLOAT)p=J.RGBA32F;if(f===J.HALF_FLOAT)p=J.RGBA16F;if(f===J.UNSIGNED_BYTE)p=EJ===W0?J.SRGB8_ALPHA8:J.RGBA8;if(f===J.UNSIGNED_SHORT_4_4_4_4)p=J.RGBA4;if(f===J.UNSIGNED_SHORT_5_5_5_1)p=J.RGB5_A1}if(p===J.R16F||p===J.R32F||p===J.RG16F||p===J.RG32F||p===J.RGBA16F||p===J.RGBA32F)Q.get("EXT_color_buffer_float");return p}function w(B,R){let f;if(B){if(R===null||R===f9||R===h9)f=J.DEPTH24_STENCIL8;else if(R===l8)f=J.DEPTH32F_STENCIL8;else if(R===U6)f=J.DEPTH24_STENCIL8,console.warn("DepthTexture: 16 bit depth attachment is not supported with stencil. Using 24-bit attachment.")}else if(R===null||R===f9||R===h9)f=J.DEPTH_COMPONENT24;else if(R===l8)f=J.DEPTH_COMPONENT32F;else if(R===U6)f=J.DEPTH_COMPONENT16;return f}function v(B,R){if(N(B)===!0||B.isFramebufferTexture&&B.minFilter!==B8&&B.minFilter!==Z8)return Math.log2(Math.max(R.width,R.height))+1;else if(B.mipmaps!==void 0&&B.mipmaps.length>0)return B.mipmaps.length;else if(B.isCompressedTexture&&Array.isArray(B.image))return R.mipmaps.length;else return 1}function _(B){let R=B.target;if(R.removeEventListener("dispose",_),x(R),R.isVideoTexture)G.delete(R)}function T(B){let R=B.target;R.removeEventListener("dispose",T),V(R)}function x(B){let R=Z.get(B);if(R.__webglInit===void 0)return;let f=B.source,n=E.get(f);if(n){let o=n[R.__cacheKey];if(o.usedTimes--,o.usedTimes===0)z(B);if(Object.keys(n).length===0)E.delete(f)}Z.remove(B)}function z(B){let R=Z.get(B);J.deleteTexture(R.__webglTexture);let f=B.source,n=E.get(f);delete n[R.__cacheKey],Y.memory.textures--}function V(B){let R=Z.get(B);if(B.depthTexture)B.depthTexture.dispose(),Z.remove(B.depthTexture);if(B.isWebGLCubeRenderTarget)for(let n=0;n<6;n++){if(Array.isArray(R.__webglFramebuffer[n]))for(let o=0;o<R.__webglFramebuffer[n].length;o++)J.deleteFramebuffer(R.__webglFramebuffer[n][o]);else J.deleteFramebuffer(R.__webglFramebuffer[n]);if(R.__webglDepthbuffer)J.deleteRenderbuffer(R.__webglDepthbuffer[n])}else{if(Array.isArray(R.__webglFramebuffer))for(let n=0;n<R.__webglFramebuffer.length;n++)J.deleteFramebuffer(R.__webglFramebuffer[n]);else J.deleteFramebuffer(R.__webglFramebuffer);if(R.__webglDepthbuffer)J.deleteRenderbuffer(R.__webglDepthbuffer);if(R.__webglMultisampledFramebuffer)J.deleteFramebuffer(R.__webglMultisampledFramebuffer);if(R.__webglColorRenderbuffer){for(let n=0;n<R.__webglColorRenderbuffer.length;n++)if(R.__webglColorRenderbuffer[n])J.deleteRenderbuffer(R.__webglColorRenderbuffer[n])}if(R.__webglDepthRenderbuffer)J.deleteRenderbuffer(R.__webglDepthRenderbuffer)}let f=B.textures;for(let n=0,o=f.length;n<o;n++){let p=Z.get(f[n]);if(p.__webglTexture)J.deleteTexture(p.__webglTexture),Y.memory.textures--;Z.remove(f[n])}Z.remove(B)}let j=0;function m(){j=0}function l(){let B=j;if(B>=W.maxTextures)console.warn("THREE.WebGLTextures: Trying to use "+B+" texture units while this GPU supports only "+W.maxTextures);return j+=1,B}function c(B){let R=[];return R.push(B.wrapS),R.push(B.wrapT),R.push(B.wrapR||0),R.push(B.magFilter),R.push(B.minFilter),R.push(B.anisotropy),R.push(B.internalFormat),R.push(B.format),R.push(B.type),R.push(B.generateMipmaps),R.push(B.premultiplyAlpha),R.push(B.flipY),R.push(B.unpackAlignment),R.push(B.colorSpace),R.join()}function i(B,R){let f=Z.get(B);if(B.isVideoTexture)V0(B);if(B.isRenderTargetTexture===!1&&B.isExternalTexture!==!0&&B.version>0&&f.__version!==B.version){let n=B.image;if(n===null)console.warn("THREE.WebGLRenderer: Texture marked for update but no image data found.");else if(n.complete===!1)console.warn("THREE.WebGLRenderer: Texture marked for update but image is incomplete");else{MJ(f,B,R);return}}else if(B.isExternalTexture)f.__webglTexture=B.sourceTexture?B.sourceTexture:null;$.bindTexture(J.TEXTURE_2D,f.__webglTexture,J.TEXTURE0+R)}function u(B,R){let f=Z.get(B);if(B.isRenderTargetTexture===!1&&B.version>0&&f.__version!==B.version){MJ(f,B,R);return}$.bindTexture(J.TEXTURE_2D_ARRAY,f.__webglTexture,J.TEXTURE0+R)}function r(B,R){let f=Z.get(B);if(B.isRenderTargetTexture===!1&&B.version>0&&f.__version!==B.version){MJ(f,B,R);return}$.bindTexture(J.TEXTURE_3D,f.__webglTexture,J.TEXTURE0+R)}function g(B,R){let f=Z.get(B);if(B.version>0&&f.__version!==B.version){GJ(f,B,R);return}$.bindTexture(J.TEXTURE_CUBE_MAP,f.__webglTexture,J.TEXTURE0+R)}let ZJ={[y9]:J.REPEAT,[G7]:J.CLAMP_TO_EDGE,[q7]:J.MIRRORED_REPEAT},UJ={[B8]:J.NEAREST,[E7]:J.NEAREST_MIPMAP_NEAREST,[H9]:J.NEAREST_MIPMAP_LINEAR,[Z8]:J.LINEAR,[v9]:J.LINEAR_MIPMAP_NEAREST,[C8]:J.LINEAR_MIPMAP_LINEAR},TJ={[yW]:J.NEVER,[gW]:J.ALWAYS,[vW]:J.LESS,[G$]:J.LEQUAL,[fW]:J.EQUAL,[xW]:J.GEQUAL,[hW]:J.GREATER,[bW]:J.NOTEQUAL};function mJ(B,R){if(R.type===l8&&Q.has("OES_texture_float_linear")===!1&&(R.magFilter===Z8||R.magFilter===v9||R.magFilter===H9||R.magFilter===C8||R.minFilter===Z8||R.minFilter===v9||R.minFilter===H9||R.minFilter===C8))console.warn("THREE.WebGLRenderer: Unable to use linear filtering with floating point textures. OES_texture_float_linear not supported on this device.");if(J.texParameteri(B,J.TEXTURE_WRAP_S,ZJ[R.wrapS]),J.texParameteri(B,J.TEXTURE_WRAP_T,ZJ[R.wrapT]),B===J.TEXTURE_3D||B===J.TEXTURE_2D_ARRAY)J.texParameteri(B,J.TEXTURE_WRAP_R,ZJ[R.wrapR]);if(J.texParameteri(B,J.TEXTURE_MAG_FILTER,UJ[R.magFilter]),J.texParameteri(B,J.TEXTURE_MIN_FILTER,UJ[R.minFilter]),R.compareFunction)J.texParameteri(B,J.TEXTURE_COMPARE_MODE,J.COMPARE_REF_TO_TEXTURE),J.texParameteri(B,J.TEXTURE_COMPARE_FUNC,TJ[R.compareFunction]);if(Q.has("EXT_texture_filter_anisotropic")===!0){if(R.magFilter===B8)return;if(R.minFilter!==H9&&R.minFilter!==C8)return;if(R.type===l8&&Q.has("OES_texture_float_linear")===!1)return;if(R.anisotropy>1||Z.get(R).__currentAnisotropy){let f=Q.get("EXT_texture_filter_anisotropic");J.texParameterf(B,f.TEXTURE_MAX_ANISOTROPY_EXT,Math.min(R.anisotropy,W.getMaxAnisotropy())),Z.get(R).__currentAnisotropy=R.anisotropy}}}function Y0(B,R){let f=!1;if(B.__webglInit===void 0)B.__webglInit=!0,R.addEventListener("dispose",_);let n=R.source,o=E.get(n);if(o===void 0)o={},E.set(n,o);let p=c(R);if(p!==B.__cacheKey){if(o[p]===void 0)o[p]={texture:J.createTexture(),usedTimes:0},Y.memory.textures++,f=!0;o[p].usedTimes++;let EJ=o[B.__cacheKey];if(EJ!==void 0){if(o[B.__cacheKey].usedTimes--,EJ.usedTimes===0)z(R)}B.__cacheKey=p,B.__webglTexture=o[p].texture}return f}function d(B,R,f){return Math.floor(Math.floor(B/f)/R)}function WJ(B,R,f,n){let p=B.updateRanges;if(p.length===0)$.texSubImage2D(J.TEXTURE_2D,0,0,0,R.width,R.height,f,n,R.data);else{p.sort((e,XJ)=>e.start-XJ.start);let EJ=0;for(let e=1;e<p.length;e++){let XJ=p[EJ],LJ=p[e],VJ=XJ.start+XJ.count,KJ=d(LJ.start,R.width,4),bJ=d(XJ.start,R.width,4);if(LJ.start<=VJ+1&&KJ===bJ&&d(LJ.start+LJ.count-1,R.width,4)===KJ)XJ.count=Math.max(XJ.count,LJ.start+LJ.count-XJ.start);else++EJ,p[EJ]=LJ}p.length=EJ+1;let JJ=J.getParameter(J.UNPACK_ROW_LENGTH),kJ=J.getParameter(J.UNPACK_SKIP_PIXELS),AJ=J.getParameter(J.UNPACK_SKIP_ROWS);J.pixelStorei(J.UNPACK_ROW_LENGTH,R.width);for(let e=0,XJ=p.length;e<XJ;e++){let LJ=p[e],VJ=Math.floor(LJ.start/4),KJ=Math.ceil(LJ.count/4),bJ=VJ%R.width,P=Math.floor(VJ/R.width),HJ=KJ,QJ=1;J.pixelStorei(J.UNPACK_SKIP_PIXELS,bJ),J.pixelStorei(J.UNPACK_SKIP_ROWS,P),$.texSubImage2D(J.TEXTURE_2D,0,bJ,P,HJ,1,f,n,R.data)}B.clearUpdateRanges(),J.pixelStorei(J.UNPACK_ROW_LENGTH,JJ),J.pixelStorei(J.UNPACK_SKIP_PIXELS,kJ),J.pixelStorei(J.UNPACK_SKIP_ROWS,AJ)}}function MJ(B,R,f){let n=J.TEXTURE_2D;if(R.isDataArrayTexture||R.isCompressedArrayTexture)n=J.TEXTURE_2D_ARRAY;if(R.isData3DTexture)n=J.TEXTURE_3D;let o=Y0(B,R),p=R.source;$.bindTexture(n,B.__webglTexture,J.TEXTURE0+f);let EJ=Z.get(p);if(p.version!==EJ.__version||o===!0){$.activeTexture(J.TEXTURE0+f);let JJ=lJ.getPrimaries(lJ.workingColorSpace),kJ=R.colorSpace===Y9?null:lJ.getPrimaries(R.colorSpace),AJ=R.colorSpace===Y9||JJ===kJ?J.NONE:J.BROWSER_DEFAULT_WEBGL;J.pixelStorei(J.UNPACK_FLIP_Y_WEBGL,R.flipY),J.pixelStorei(J.UNPACK_PREMULTIPLY_ALPHA_WEBGL,R.premultiplyAlpha),J.pixelStorei(J.UNPACK_ALIGNMENT,R.unpackAlignment),J.pixelStorei(J.UNPACK_COLORSPACE_CONVERSION_WEBGL,AJ);let e=M(R.image,!1,W.maxTextureSize);e=D0(R,e);let XJ=H.convert(R.format,R.colorSpace),LJ=H.convert(R.type),VJ=L(R.internalFormat,XJ,LJ,R.colorSpace,R.isVideoTexture);mJ(n,R);let KJ,bJ=R.mipmaps,P=R.isVideoTexture!==!0,HJ=EJ.__version===void 0||o===!0,QJ=p.dataReady,NJ=v(R,e);if(R.isDepthTexture){if(VJ=w(R.format===q6,R.type),HJ)if(P)$.texStorage2D(J.TEXTURE_2D,1,VJ,e.width,e.height);else $.texImage2D(J.TEXTURE_2D,0,VJ,e.width,e.height,0,XJ,LJ,null)}else if(R.isDataTexture)if(bJ.length>0){if(P&&HJ)$.texStorage2D(J.TEXTURE_2D,NJ,VJ,bJ[0].width,bJ[0].height);for(let a=0,s=bJ.length;a<s;a++)if(KJ=bJ[a],P){if(QJ)$.texSubImage2D(J.TEXTURE_2D,a,0,0,KJ.width,KJ.height,XJ,LJ,KJ.data)}else $.texImage2D(J.TEXTURE_2D,a,VJ,KJ.width,KJ.height,0,XJ,LJ,KJ.data);R.generateMipmaps=!1}else if(P){if(HJ)$.texStorage2D(J.TEXTURE_2D,NJ,VJ,e.width,e.height);if(QJ)WJ(R,e,XJ,LJ)}else $.texImage2D(J.TEXTURE_2D,0,VJ,e.width,e.height,0,XJ,LJ,e.data);else if(R.isCompressedTexture)if(R.isCompressedArrayTexture){if(P&&HJ)$.texStorage3D(J.TEXTURE_2D_ARRAY,NJ,VJ,bJ[0].width,bJ[0].height,e.depth);for(let a=0,s=bJ.length;a<s;a++)if(KJ=bJ[a],R.format!==U8)if(XJ!==null)if(P){if(QJ)if(R.layerUpdates.size>0){let FJ=j$(KJ.width,KJ.height,R.format,R.type);for(let yJ of R.layerUpdates){let J0=KJ.data.subarray(yJ*FJ/KJ.data.BYTES_PER_ELEMENT,(yJ+1)*FJ/KJ.data.BYTES_PER_ELEMENT);$.compressedTexSubImage3D(J.TEXTURE_2D_ARRAY,a,0,0,yJ,KJ.width,KJ.height,1,XJ,J0)}R.clearLayerUpdates()}else $.compressedTexSubImage3D(J.TEXTURE_2D_ARRAY,a,0,0,0,KJ.width,KJ.height,e.depth,XJ,KJ.data)}else $.compressedTexImage3D(J.TEXTURE_2D_ARRAY,a,VJ,KJ.width,KJ.height,e.depth,0,KJ.data,0,0);else console.warn("THREE.WebGLRenderer: Attempt to load unsupported compressed texture format in .uploadTexture()");else if(P){if(QJ)$.texSubImage3D(J.TEXTURE_2D_ARRAY,a,0,0,0,KJ.width,KJ.height,e.depth,XJ,LJ,KJ.data)}else $.texImage3D(J.TEXTURE_2D_ARRAY,a,VJ,KJ.width,KJ.height,e.depth,0,XJ,LJ,KJ.data)}else{if(P&&HJ)$.texStorage2D(J.TEXTURE_2D,NJ,VJ,bJ[0].width,bJ[0].height);for(let a=0,s=bJ.length;a<s;a++)if(KJ=bJ[a],R.format!==U8)if(XJ!==null)if(P){if(QJ)$.compressedTexSubImage2D(J.TEXTURE_2D,a,0,0,KJ.width,KJ.height,XJ,KJ.data)}else $.compressedTexImage2D(J.TEXTURE_2D,a,VJ,KJ.width,KJ.height,0,KJ.data);else console.warn("THREE.WebGLRenderer: Attempt to load unsupported compressed texture format in .uploadTexture()");else if(P){if(QJ)$.texSubImage2D(J.TEXTURE_2D,a,0,0,KJ.width,KJ.height,XJ,LJ,KJ.data)}else $.texImage2D(J.TEXTURE_2D,a,VJ,KJ.width,KJ.height,0,XJ,LJ,KJ.data)}else if(R.isDataArrayTexture)if(P){if(HJ)$.texStorage3D(J.TEXTURE_2D_ARRAY,NJ,VJ,e.width,e.height,e.depth);if(QJ)if(R.layerUpdates.size>0){let a=j$(e.width,e.height,R.format,R.type);for(let s of R.layerUpdates){let FJ=e.data.subarray(s*a/e.data.BYTES_PER_ELEMENT,(s+1)*a/e.data.BYTES_PER_ELEMENT);$.texSubImage3D(J.TEXTURE_2D_ARRAY,0,0,0,s,e.width,e.height,1,XJ,LJ,FJ)}R.clearLayerUpdates()}else $.texSubImage3D(J.TEXTURE_2D_ARRAY,0,0,0,0,e.width,e.height,e.depth,XJ,LJ,e.data)}else $.texImage3D(J.TEXTURE_2D_ARRAY,0,VJ,e.width,e.height,e.depth,0,XJ,LJ,e.data);else if(R.isData3DTexture)if(P){if(HJ)$.texStorage3D(J.TEXTURE_3D,NJ,VJ,e.width,e.height,e.depth);if(QJ)$.texSubImage3D(J.TEXTURE_3D,0,0,0,0,e.width,e.height,e.depth,XJ,LJ,e.data)}else $.texImage3D(J.TEXTURE_3D,0,VJ,e.width,e.height,e.depth,0,XJ,LJ,e.data);else if(R.isFramebufferTexture){if(HJ)if(P)$.texStorage2D(J.TEXTURE_2D,NJ,VJ,e.width,e.height);else{let{width:a,height:s}=e;for(let FJ=0;FJ<NJ;FJ++)$.texImage2D(J.TEXTURE_2D,FJ,VJ,a,s,0,XJ,LJ,null),a>>=1,s>>=1}}else if(bJ.length>0){if(P&&HJ){let a=N0(bJ[0]);$.texStorage2D(J.TEXTURE_2D,NJ,VJ,a.width,a.height)}for(let a=0,s=bJ.length;a<s;a++)if(KJ=bJ[a],P){if(QJ)$.texSubImage2D(J.TEXTURE_2D,a,0,0,XJ,LJ,KJ)}else $.texImage2D(J.TEXTURE_2D,a,VJ,XJ,LJ,KJ);R.generateMipmaps=!1}else if(P){if(HJ){let a=N0(e);$.texStorage2D(J.TEXTURE_2D,NJ,VJ,a.width,a.height)}if(QJ)$.texSubImage2D(J.TEXTURE_2D,0,0,0,XJ,LJ,e)}else $.texImage2D(J.TEXTURE_2D,0,VJ,XJ,LJ,e);if(N(R))O(n);if(EJ.__version=p.version,R.onUpdate)R.onUpdate(R)}B.__version=R.version}function GJ(B,R,f){if(R.image.length!==6)return;let n=Y0(B,R),o=R.source;$.bindTexture(J.TEXTURE_CUBE_MAP,B.__webglTexture,J.TEXTURE0+f);let p=Z.get(o);if(o.version!==p.__version||n===!0){$.activeTexture(J.TEXTURE0+f);let EJ=lJ.getPrimaries(lJ.workingColorSpace),JJ=R.colorSpace===Y9?null:lJ.getPrimaries(R.colorSpace),kJ=R.colorSpace===Y9||EJ===JJ?J.NONE:J.BROWSER_DEFAULT_WEBGL;J.pixelStorei(J.UNPACK_FLIP_Y_WEBGL,R.flipY),J.pixelStorei(J.UNPACK_PREMULTIPLY_ALPHA_WEBGL,R.premultiplyAlpha),J.pixelStorei(J.UNPACK_ALIGNMENT,R.unpackAlignment),J.pixelStorei(J.UNPACK_COLORSPACE_CONVERSION_WEBGL,kJ);let AJ=R.isCompressedTexture||R.image[0].isCompressedTexture,e=R.image[0]&&R.image[0].isDataTexture,XJ=[];for(let s=0;s<6;s++){if(!AJ&&!e)XJ[s]=M(R.image[s],!0,W.maxCubemapSize);else XJ[s]=e?R.image[s].image:R.image[s];XJ[s]=D0(R,XJ[s])}let LJ=XJ[0],VJ=H.convert(R.format,R.colorSpace),KJ=H.convert(R.type),bJ=L(R.internalFormat,VJ,KJ,R.colorSpace),P=R.isVideoTexture!==!0,HJ=p.__version===void 0||n===!0,QJ=o.dataReady,NJ=v(R,LJ);mJ(J.TEXTURE_CUBE_MAP,R);let a;if(AJ){if(P&&HJ)$.texStorage2D(J.TEXTURE_CUBE_MAP,NJ,bJ,LJ.width,LJ.height);for(let s=0;s<6;s++){a=XJ[s].mipmaps;for(let FJ=0;FJ<a.length;FJ++){let yJ=a[FJ];if(R.format!==U8)if(VJ!==null)if(P){if(QJ)$.compressedTexSubImage2D(J.TEXTURE_CUBE_MAP_POSITIVE_X+s,FJ,0,0,yJ.width,yJ.height,VJ,yJ.data)}else $.compressedTexImage2D(J.TEXTURE_CUBE_MAP_POSITIVE_X+s,FJ,bJ,yJ.width,yJ.height,0,yJ.data);else console.warn("THREE.WebGLRenderer: Attempt to load unsupported compressed texture format in .setTextureCube()");else if(P){if(QJ)$.texSubImage2D(J.TEXTURE_CUBE_MAP_POSITIVE_X+s,FJ,0,0,yJ.width,yJ.height,VJ,KJ,yJ.data)}else $.texImage2D(J.TEXTURE_CUBE_MAP_POSITIVE_X+s,FJ,bJ,yJ.width,yJ.height,0,VJ,KJ,yJ.data)}}}else{if(a=R.mipmaps,P&&HJ){if(a.length>0)NJ++;let s=N0(XJ[0]);$.texStorage2D(J.TEXTURE_CUBE_MAP,NJ,bJ,s.width,s.height)}for(let s=0;s<6;s++)if(e){if(P){if(QJ)$.texSubImage2D(J.TEXTURE_CUBE_MAP_POSITIVE_X+s,0,0,0,XJ[s].width,XJ[s].height,VJ,KJ,XJ[s].data)}else $.texImage2D(J.TEXTURE_CUBE_MAP_POSITIVE_X+s,0,bJ,XJ[s].width,XJ[s].height,0,VJ,KJ,XJ[s].data);for(let FJ=0;FJ<a.length;FJ++){let J0=a[FJ].image[s].image;if(P){if(QJ)$.texSubImage2D(J.TEXTURE_CUBE_MAP_POSITIVE_X+s,FJ+1,0,0,J0.width,J0.height,VJ,KJ,J0.data)}else $.texImage2D(J.TEXTURE_CUBE_MAP_POSITIVE_X+s,FJ+1,bJ,J0.width,J0.height,0,VJ,KJ,J0.data)}}else{if(P){if(QJ)$.texSubImage2D(J.TEXTURE_CUBE_MAP_POSITIVE_X+s,0,0,0,VJ,KJ,XJ[s])}else $.texImage2D(J.TEXTURE_CUBE_MAP_POSITIVE_X+s,0,bJ,VJ,KJ,XJ[s]);for(let FJ=0;FJ<a.length;FJ++){let yJ=a[FJ];if(P){if(QJ)$.texSubImage2D(J.TEXTURE_CUBE_MAP_POSITIVE_X+s,FJ+1,0,0,VJ,KJ,yJ.image[s])}else $.texImage2D(J.TEXTURE_CUBE_MAP_POSITIVE_X+s,FJ+1,bJ,VJ,KJ,yJ.image[s])}}}if(N(R))O(J.TEXTURE_CUBE_MAP);if(p.__version=o.version,R.onUpdate)R.onUpdate(R)}B.__version=R.version}function RJ(B,R,f,n,o,p){let EJ=H.convert(f.format,f.colorSpace),JJ=H.convert(f.type),kJ=L(f.internalFormat,EJ,JJ,f.colorSpace),AJ=Z.get(R),e=Z.get(f);if(e.__renderTarget=R,!AJ.__hasExternalTextures){let XJ=Math.max(1,R.width>>p),LJ=Math.max(1,R.height>>p);if(o===J.TEXTURE_3D||o===J.TEXTURE_2D_ARRAY)$.texImage3D(o,p,kJ,XJ,LJ,R.depth,0,EJ,JJ,null);else $.texImage2D(o,p,kJ,XJ,LJ,0,EJ,JJ,null)}if($.bindFramebuffer(J.FRAMEBUFFER,B),_J(R))X.framebufferTexture2DMultisampleEXT(J.FRAMEBUFFER,n,o,e.__webglTexture,0,DJ(R));else if(o===J.TEXTURE_2D||o>=J.TEXTURE_CUBE_MAP_POSITIVE_X&&o<=J.TEXTURE_CUBE_MAP_NEGATIVE_Z)J.framebufferTexture2D(J.FRAMEBUFFER,n,o,e.__webglTexture,p);$.bindFramebuffer(J.FRAMEBUFFER,null)}function uJ(B,R,f){if(J.bindRenderbuffer(J.RENDERBUFFER,B),R.depthBuffer){let n=R.depthTexture,o=n&&n.isDepthTexture?n.type:null,p=w(R.stencilBuffer,o),EJ=R.stencilBuffer?J.DEPTH_STENCIL_ATTACHMENT:J.DEPTH_ATTACHMENT,JJ=DJ(R);if(_J(R))X.renderbufferStorageMultisampleEXT(J.RENDERBUFFER,JJ,p,R.width,R.height);else if(f)J.renderbufferStorageMultisample(J.RENDERBUFFER,JJ,p,R.width,R.height);else J.renderbufferStorage(J.RENDERBUFFER,p,R.width,R.height);J.framebufferRenderbuffer(J.FRAMEBUFFER,EJ,J.RENDERBUFFER,B)}else{let n=R.textures;for(let o=0;o<n.length;o++){let p=n[o],EJ=H.convert(p.format,p.colorSpace),JJ=H.convert(p.type),kJ=L(p.internalFormat,EJ,JJ,p.colorSpace),AJ=DJ(R);if(f&&_J(R)===!1)J.renderbufferStorageMultisample(J.RENDERBUFFER,AJ,kJ,R.width,R.height);else if(_J(R))X.renderbufferStorageMultisampleEXT(J.RENDERBUFFER,AJ,kJ,R.width,R.height);else J.renderbufferStorage(J.RENDERBUFFER,kJ,R.width,R.height)}}J.bindRenderbuffer(J.RENDERBUFFER,null)}function cJ(B,R){if(R&&R.isWebGLCubeRenderTarget)throw new Error("Depth Texture with cube render targets is not supported");if($.bindFramebuffer(J.FRAMEBUFFER,B),!(R.depthTexture&&R.depthTexture.isDepthTexture))throw new Error("renderTarget.depthTexture must be an instance of THREE.DepthTexture");let n=Z.get(R.depthTexture);if(n.__renderTarget=R,!n.__webglTexture||R.depthTexture.image.width!==R.width||R.depthTexture.image.height!==R.height)R.depthTexture.image.width=R.width,R.depthTexture.image.height=R.height,R.depthTexture.needsUpdate=!0;i(R.depthTexture,0);let o=n.__webglTexture,p=DJ(R);if(R.depthTexture.format===N7)if(_J(R))X.framebufferTexture2DMultisampleEXT(J.FRAMEBUFFER,J.DEPTH_ATTACHMENT,J.TEXTURE_2D,o,0,p);else J.framebufferTexture2D(J.FRAMEBUFFER,J.DEPTH_ATTACHMENT,J.TEXTURE_2D,o,0);else if(R.depthTexture.format===q6)if(_J(R))X.framebufferTexture2DMultisampleEXT(J.FRAMEBUFFER,J.DEPTH_STENCIL_ATTACHMENT,J.TEXTURE_2D,o,0,p);else J.framebufferTexture2D(J.FRAMEBUFFER,J.DEPTH_STENCIL_ATTACHMENT,J.TEXTURE_2D,o,0);else throw new Error("Unknown depthTexture format")}function dJ(B){let R=Z.get(B),f=B.isWebGLCubeRenderTarget===!0;if(R.__boundDepthTexture!==B.depthTexture){let n=B.depthTexture;if(R.__depthDisposeCallback)R.__depthDisposeCallback();if(n){let o=()=>{delete R.__boundDepthTexture,delete R.__depthDisposeCallback,n.removeEventListener("dispose",o)};n.addEventListener("dispose",o),R.__depthDisposeCallback=o}R.__boundDepthTexture=n}if(B.depthTexture&&!R.__autoAllocateDepthBuffer){if(f)throw new Error("target.depthTexture not supported in Cube render targets");let n=B.texture.mipmaps;if(n&&n.length>0)cJ(R.__webglFramebuffer[0],B);else cJ(R.__webglFramebuffer,B)}else if(f){R.__webglDepthbuffer=[];for(let n=0;n<6;n++)if($.bindFramebuffer(J.FRAMEBUFFER,R.__webglFramebuffer[n]),R.__webglDepthbuffer[n]===void 0)R.__webglDepthbuffer[n]=J.createRenderbuffer(),uJ(R.__webglDepthbuffer[n],B,!1);else{let o=B.stencilBuffer?J.DEPTH_STENCIL_ATTACHMENT:J.DEPTH_ATTACHMENT,p=R.__webglDepthbuffer[n];J.bindRenderbuffer(J.RENDERBUFFER,p),J.framebufferRenderbuffer(J.FRAMEBUFFER,o,J.RENDERBUFFER,p)}}else{let n=B.texture.mipmaps;if(n&&n.length>0)$.bindFramebuffer(J.FRAMEBUFFER,R.__webglFramebuffer[0]);else $.bindFramebuffer(J.FRAMEBUFFER,R.__webglFramebuffer);if(R.__webglDepthbuffer===void 0)R.__webglDepthbuffer=J.createRenderbuffer(),uJ(R.__webglDepthbuffer,B,!1);else{let o=B.stencilBuffer?J.DEPTH_STENCIL_ATTACHMENT:J.DEPTH_ATTACHMENT,p=R.__webglDepthbuffer;J.bindRenderbuffer(J.RENDERBUFFER,p),J.framebufferRenderbuffer(J.FRAMEBUFFER,o,J.RENDERBUFFER,p)}}$.bindFramebuffer(J.FRAMEBUFFER,null)}function I(B,R,f){let n=Z.get(B);if(R!==void 0)RJ(n.__webglFramebuffer,B,B.texture,J.COLOR_ATTACHMENT0,J.TEXTURE_2D,0);if(f!==void 0)dJ(B)}function $0(B){let R=B.texture,f=Z.get(B),n=Z.get(R);B.addEventListener("dispose",T);let o=B.textures,p=B.isWebGLCubeRenderTarget===!0,EJ=o.length>1;if(!EJ){if(n.__webglTexture===void 0)n.__webglTexture=J.createTexture();n.__version=R.version,Y.memory.textures++}if(p){f.__webglFramebuffer=[];for(let JJ=0;JJ<6;JJ++)if(R.mipmaps&&R.mipmaps.length>0){f.__webglFramebuffer[JJ]=[];for(let kJ=0;kJ<R.mipmaps.length;kJ++)f.__webglFramebuffer[JJ][kJ]=J.createFramebuffer()}else f.__webglFramebuffer[JJ]=J.createFramebuffer()}else{if(R.mipmaps&&R.mipmaps.length>0){f.__webglFramebuffer=[];for(let JJ=0;JJ<R.mipmaps.length;JJ++)f.__webglFramebuffer[JJ]=J.createFramebuffer()}else f.__webglFramebuffer=J.createFramebuffer();if(EJ)for(let JJ=0,kJ=o.length;JJ<kJ;JJ++){let AJ=Z.get(o[JJ]);if(AJ.__webglTexture===void 0)AJ.__webglTexture=J.createTexture(),Y.memory.textures++}if(B.samples>0&&_J(B)===!1){f.__webglMultisampledFramebuffer=J.createFramebuffer(),f.__webglColorRenderbuffer=[],$.bindFramebuffer(J.FRAMEBUFFER,f.__webglMultisampledFramebuffer);for(let JJ=0;JJ<o.length;JJ++){let kJ=o[JJ];f.__webglColorRenderbuffer[JJ]=J.createRenderbuffer(),J.bindRenderbuffer(J.RENDERBUFFER,f.__webglColorRenderbuffer[JJ]);let AJ=H.convert(kJ.format,kJ.colorSpace),e=H.convert(kJ.type),XJ=L(kJ.internalFormat,AJ,e,kJ.colorSpace,B.isXRRenderTarget===!0),LJ=DJ(B);J.renderbufferStorageMultisample(J.RENDERBUFFER,LJ,XJ,B.width,B.height),J.framebufferRenderbuffer(J.FRAMEBUFFER,J.COLOR_ATTACHMENT0+JJ,J.RENDERBUFFER,f.__webglColorRenderbuffer[JJ])}if(J.bindRenderbuffer(J.RENDERBUFFER,null),B.depthBuffer)f.__webglDepthRenderbuffer=J.createRenderbuffer(),uJ(f.__webglDepthRenderbuffer,B,!0);$.bindFramebuffer(J.FRAMEBUFFER,null)}}if(p){$.bindTexture(J.TEXTURE_CUBE_MAP,n.__webglTexture),mJ(J.TEXTURE_CUBE_MAP,R);for(let JJ=0;JJ<6;JJ++)if(R.mipmaps&&R.mipmaps.length>0)for(let kJ=0;kJ<R.mipmaps.length;kJ++)RJ(f.__webglFramebuffer[JJ][kJ],B,R,J.COLOR_ATTACHMENT0,J.TEXTURE_CUBE_MAP_POSITIVE_X+JJ,kJ);else RJ(f.__webglFramebuffer[JJ],B,R,J.COLOR_ATTACHMENT0,J.TEXTURE_CUBE_MAP_POSITIVE_X+JJ,0);if(N(R))O(J.TEXTURE_CUBE_MAP);$.unbindTexture()}else if(EJ){for(let JJ=0,kJ=o.length;JJ<kJ;JJ++){let AJ=o[JJ],e=Z.get(AJ),XJ=J.TEXTURE_2D;if(B.isWebGL3DRenderTarget||B.isWebGLArrayRenderTarget)XJ=B.isWebGL3DRenderTarget?J.TEXTURE_3D:J.TEXTURE_2D_ARRAY;if($.bindTexture(XJ,e.__webglTexture),mJ(XJ,AJ),RJ(f.__webglFramebuffer,B,AJ,J.COLOR_ATTACHMENT0+JJ,XJ,0),N(AJ))O(XJ)}$.unbindTexture()}else{let JJ=J.TEXTURE_2D;if(B.isWebGL3DRenderTarget||B.isWebGLArrayRenderTarget)JJ=B.isWebGL3DRenderTarget?J.TEXTURE_3D:J.TEXTURE_2D_ARRAY;if($.bindTexture(JJ,n.__webglTexture),mJ(JJ,R),R.mipmaps&&R.mipmaps.length>0)for(let kJ=0;kJ<R.mipmaps.length;kJ++)RJ(f.__webglFramebuffer[kJ],B,R,J.COLOR_ATTACHMENT0,JJ,kJ);else RJ(f.__webglFramebuffer,B,R,J.COLOR_ATTACHMENT0,JJ,0);if(N(R))O(JJ);$.unbindTexture()}if(B.depthBuffer)dJ(B)}function CJ(B){let R=B.textures;for(let f=0,n=R.length;f<n;f++){let o=R[f];if(N(o)){let p=C(B),EJ=Z.get(o).__webglTexture;$.bindTexture(p,EJ),O(p),$.unbindTexture()}}}let iJ=[],zJ=[];function X0(B){if(B.samples>0){if(_J(B)===!1){let{textures:R,width:f,height:n}=B,o=J.COLOR_BUFFER_BIT,p=B.stencilBuffer?J.DEPTH_STENCIL_ATTACHMENT:J.DEPTH_ATTACHMENT,EJ=Z.get(B),JJ=R.length>1;if(JJ)for(let AJ=0;AJ<R.length;AJ++)$.bindFramebuffer(J.FRAMEBUFFER,EJ.__webglMultisampledFramebuffer),J.framebufferRenderbuffer(J.FRAMEBUFFER,J.COLOR_ATTACHMENT0+AJ,J.RENDERBUFFER,null),$.bindFramebuffer(J.FRAMEBUFFER,EJ.__webglFramebuffer),J.framebufferTexture2D(J.DRAW_FRAMEBUFFER,J.COLOR_ATTACHMENT0+AJ,J.TEXTURE_2D,null,0);$.bindFramebuffer(J.READ_FRAMEBUFFER,EJ.__webglMultisampledFramebuffer);let kJ=B.texture.mipmaps;if(kJ&&kJ.length>0)$.bindFramebuffer(J.DRAW_FRAMEBUFFER,EJ.__webglFramebuffer[0]);else $.bindFramebuffer(J.DRAW_FRAMEBUFFER,EJ.__webglFramebuffer);for(let AJ=0;AJ<R.length;AJ++){if(B.resolveDepthBuffer){if(B.depthBuffer)o|=J.DEPTH_BUFFER_BIT;if(B.stencilBuffer&&B.resolveStencilBuffer)o|=J.STENCIL_BUFFER_BIT}if(JJ){J.framebufferRenderbuffer(J.READ_FRAMEBUFFER,J.COLOR_ATTACHMENT0,J.RENDERBUFFER,EJ.__webglColorRenderbuffer[AJ]);let e=Z.get(R[AJ]).__webglTexture;J.framebufferTexture2D(J.DRAW_FRAMEBUFFER,J.COLOR_ATTACHMENT0,J.TEXTURE_2D,e,0)}if(J.blitFramebuffer(0,0,f,n,0,0,f,n,o,J.NEAREST),K===!0){if(iJ.length=0,zJ.length=0,iJ.push(J.COLOR_ATTACHMENT0+AJ),B.depthBuffer&&B.resolveDepthBuffer===!1)iJ.push(p),zJ.push(p),J.invalidateFramebuffer(J.DRAW_FRAMEBUFFER,zJ);J.invalidateFramebuffer(J.READ_FRAMEBUFFER,iJ)}}if($.bindFramebuffer(J.READ_FRAMEBUFFER,null),$.bindFramebuffer(J.DRAW_FRAMEBUFFER,null),JJ)for(let AJ=0;AJ<R.length;AJ++){$.bindFramebuffer(J.FRAMEBUFFER,EJ.__webglMultisampledFramebuffer),J.framebufferRenderbuffer(J.FRAMEBUFFER,J.COLOR_ATTACHMENT0+AJ,J.RENDERBUFFER,EJ.__webglColorRenderbuffer[AJ]);let e=Z.get(R[AJ]).__webglTexture;$.bindFramebuffer(J.FRAMEBUFFER,EJ.__webglFramebuffer),J.framebufferTexture2D(J.DRAW_FRAMEBUFFER,J.COLOR_ATTACHMENT0+AJ,J.TEXTURE_2D,e,0)}$.bindFramebuffer(J.DRAW_FRAMEBUFFER,EJ.__webglMultisampledFramebuffer)}else if(B.depthBuffer&&B.resolveDepthBuffer===!1&&K){let R=B.stencilBuffer?J.DEPTH_STENCIL_ATTACHMENT:J.DEPTH_ATTACHMENT;J.invalidateFramebuffer(J.DRAW_FRAMEBUFFER,[R])}}}function DJ(B){return Math.min(W.maxSamples,B.samples)}function _J(B){let R=Z.get(B);return B.samples>0&&Q.has("WEBGL_multisampled_render_to_texture")===!0&&R.__useRenderToTexture!==!1}function V0(B){let R=Y.render.frame;if(G.get(B)!==R)G.set(B,R),B.update()}function D0(B,R){let{colorSpace:f,format:n,type:o}=B;if(B.isCompressedTexture===!0||B.isVideoTexture===!0)return R;if(f!==P0&&f!==Y9)if(lJ.getTransfer(f)===W0){if(n!==U8||o!==p8)console.warn("THREE.WebGLTextures: sRGB encoded textures have to use RGBAFormat and UnsignedByteType.")}else console.error("THREE.WebGLTextures: Unsupported texture color space:",f);return R}function N0(B){if(typeof HTMLImageElement!=="undefined"&&B instanceof HTMLImageElement)U.width=B.naturalWidth||B.width,U.height=B.naturalHeight||B.height;else if(typeof VideoFrame!=="undefined"&&B instanceof VideoFrame)U.width=B.displayWidth,U.height=B.displayHeight;else U.width=B.width,U.height=B.height;return U}this.allocateTextureUnit=l,this.resetTextureUnits=m,this.setTexture2D=i,this.setTexture2DArray=u,this.setTexture3D=r,this.setTextureCube=g,this.rebindTextures=I,this.setupRenderTarget=$0,this.updateRenderTargetMipmap=CJ,this.updateMultisampleRenderTarget=X0,this.setupDepthRenderbuffer=dJ,this.setupFrameBufferTexture=RJ,this.useMultisampledRTT=_J}function b1(J,Q){function $(Z,W=Y9){let H,Y=lJ.getTransfer(W);if(Z===p8)return J.UNSIGNED_BYTE;if(Z===AQ)return J.UNSIGNED_SHORT_4_4_4_4;if(Z===SQ)return J.UNSIGNED_SHORT_5_5_5_1;if(Z===CW)return J.UNSIGNED_INT_5_9_9_9_REV;if(Z===zW)return J.BYTE;if(Z===BW)return J.SHORT;if(Z===U6)return J.UNSIGNED_SHORT;if(Z===TQ)return J.INT;if(Z===f9)return J.UNSIGNED_INT;if(Z===l8)return J.FLOAT;if(Z===G6)return J.HALF_FLOAT;if(Z===wW)return J.ALPHA;if(Z===_W)return J.RGB;if(Z===U8)return J.RGBA;if(Z===N7)return J.DEPTH_COMPONENT;if(Z===q6)return J.DEPTH_STENCIL;if(Z===IW)return J.RED;if(Z===jQ)return J.RED_INTEGER;if(Z===PW)return J.RG;if(Z===yQ)return J.RG_INTEGER;if(Z===vQ)return J.RGBA_INTEGER;if(Z===O7||Z===F7||Z===R7||Z===k7)if(Y===W0)if(H=Q.get("WEBGL_compressed_texture_s3tc_srgb"),H!==null){if(Z===O7)return H.COMPRESSED_SRGB_S3TC_DXT1_EXT;if(Z===F7)return H.COMPRESSED_SRGB_ALPHA_S3TC_DXT1_EXT;if(Z===R7)return H.COMPRESSED_SRGB_ALPHA_S3TC_DXT3_EXT;if(Z===k7)return H.COMPRESSED_SRGB_ALPHA_S3TC_DXT5_EXT}else return null;else if(H=Q.get("WEBGL_compressed_texture_s3tc"),H!==null){if(Z===O7)return H.COMPRESSED_RGB_S3TC_DXT1_EXT;if(Z===F7)return H.COMPRESSED_RGBA_S3TC_DXT1_EXT;if(Z===R7)return H.COMPRESSED_RGBA_S3TC_DXT3_EXT;if(Z===k7)return H.COMPRESSED_RGBA_S3TC_DXT5_EXT}else return null;if(Z===fQ||Z===hQ||Z===bQ||Z===xQ)if(H=Q.get("WEBGL_compressed_texture_pvrtc"),H!==null){if(Z===fQ)return H.COMPRESSED_RGB_PVRTC_4BPPV1_IMG;if(Z===hQ)return H.COMPRESSED_RGB_PVRTC_2BPPV1_IMG;if(Z===bQ)return H.COMPRESSED_RGBA_PVRTC_4BPPV1_IMG;if(Z===xQ)return H.COMPRESSED_RGBA_PVRTC_2BPPV1_IMG}else return null;if(Z===gQ||Z===pQ||Z===lQ)if(H=Q.get("WEBGL_compressed_texture_etc"),H!==null){if(Z===gQ||Z===pQ)return Y===W0?H.COMPRESSED_SRGB8_ETC2:H.COMPRESSED_RGB8_ETC2;if(Z===lQ)return Y===W0?H.COMPRESSED_SRGB8_ALPHA8_ETC2_EAC:H.COMPRESSED_RGBA8_ETC2_EAC}else return null;if(Z===dQ||Z===mQ||Z===uQ||Z===cQ||Z===nQ||Z===sQ||Z===oQ||Z===iQ||Z===aQ||Z===rQ||Z===tQ||Z===eQ||Z===J$||Z===Q$)if(H=Q.get("WEBGL_compressed_texture_astc"),H!==null){if(Z===dQ)return Y===W0?H.COMPRESSED_SRGB8_ALPHA8_ASTC_4x4_KHR:H.COMPRESSED_RGBA_ASTC_4x4_KHR;if(Z===mQ)return Y===W0?H.COMPRESSED_SRGB8_ALPHA8_ASTC_5x4_KHR:H.COMPRESSED_RGBA_ASTC_5x4_KHR;if(Z===uQ)return Y===W0?H.COMPRESSED_SRGB8_ALPHA8_ASTC_5x5_KHR:H.COMPRESSED_RGBA_ASTC_5x5_KHR;if(Z===cQ)return Y===W0?H.COMPRESSED_SRGB8_ALPHA8_ASTC_6x5_KHR:H.COMPRESSED_RGBA_ASTC_6x5_KHR;if(Z===nQ)return Y===W0?H.COMPRESSED_SRGB8_ALPHA8_ASTC_6x6_KHR:H.COMPRESSED_RGBA_ASTC_6x6_KHR;if(Z===sQ)return Y===W0?H.COMPRESSED_SRGB8_ALPHA8_ASTC_8x5_KHR:H.COMPRESSED_RGBA_ASTC_8x5_KHR;if(Z===oQ)return Y===W0?H.COMPRESSED_SRGB8_ALPHA8_ASTC_8x6_KHR:H.COMPRESSED_RGBA_ASTC_8x6_KHR;if(Z===iQ)return Y===W0?H.COMPRESSED_SRGB8_ALPHA8_ASTC_8x8_KHR:H.COMPRESSED_RGBA_ASTC_8x8_KHR;if(Z===aQ)return Y===W0?H.COMPRESSED_SRGB8_ALPHA8_ASTC_10x5_KHR:H.COMPRESSED_RGBA_ASTC_10x5_KHR;if(Z===rQ)return Y===W0?H.COMPRESSED_SRGB8_ALPHA8_ASTC_10x6_KHR:H.COMPRESSED_RGBA_ASTC_10x6_KHR;if(Z===tQ)return Y===W0?H.COMPRESSED_SRGB8_ALPHA8_ASTC_10x8_KHR:H.COMPRESSED_RGBA_ASTC_10x8_KHR;if(Z===eQ)return Y===W0?H.COMPRESSED_SRGB8_ALPHA8_ASTC_10x10_KHR:H.COMPRESSED_RGBA_ASTC_10x10_KHR;if(Z===J$)return Y===W0?H.COMPRESSED_SRGB8_ALPHA8_ASTC_12x10_KHR:H.COMPRESSED_RGBA_ASTC_12x10_KHR;if(Z===Q$)return Y===W0?H.COMPRESSED_SRGB8_ALPHA8_ASTC_12x12_KHR:H.COMPRESSED_RGBA_ASTC_12x12_KHR}else return null;if(Z===M7||Z===$$||Z===Z$)if(H=Q.get("EXT_texture_compression_bptc"),H!==null){if(Z===M7)return Y===W0?H.COMPRESSED_SRGB_ALPHA_BPTC_UNORM_EXT:H.COMPRESSED_RGBA_BPTC_UNORM_EXT;if(Z===$$)return H.COMPRESSED_RGB_BPTC_SIGNED_FLOAT_EXT;if(Z===Z$)return H.COMPRESSED_RGB_BPTC_UNSIGNED_FLOAT_EXT}else return null;if(Z===TW||Z===W$||Z===H$||Z===Y$)if(H=Q.get("EXT_texture_compression_rgtc"),H!==null){if(Z===M7)return H.COMPRESSED_RED_RGTC1_EXT;if(Z===W$)return H.COMPRESSED_SIGNED_RED_RGTC1_EXT;if(Z===H$)return H.COMPRESSED_RED_GREEN_RGTC2_EXT;if(Z===Y$)return H.COMPRESSED_SIGNED_RED_GREEN_RGTC2_EXT}else return null;if(Z===h9)return J.UNSIGNED_INT_24_8;return J[Z]!==void 0?J[Z]:null}return{convert:$}}class d$ extends E0{constructor(J=null){super();this.sourceTexture=J,this.isExternalTexture=!0}}var x1=`
void main() {

	gl_Position = vec4( position, 1.0 );

}`,g1=`
uniform sampler2DArray depthColor;
uniform float depthWidth;
uniform float depthHeight;

void main() {

	vec2 coord = vec2( gl_FragCoord.x / depthWidth, gl_FragCoord.y / depthHeight );

	if ( coord.x >= 1.0 ) {

		gl_FragDepth = texture( depthColor, vec3( coord.x - 1.0, coord.y, 1 ) ).r;

	} else {

		gl_FragDepth = texture( depthColor, vec3( coord.x, coord.y, 0 ) ).r;

	}

}`;class AH{constructor(){this.texture=null,this.mesh=null,this.depthNear=0,this.depthFar=0}init(J,Q){if(this.texture===null){let $=new d$(J.texture);if(J.depthNear!==Q.depthNear||J.depthFar!==Q.depthFar)this.depthNear=J.depthNear,this.depthFar=J.depthFar;this.texture=$}}getMesh(J){if(this.texture!==null){if(this.mesh===null){let Q=J.cameras[0].viewport,$=new q8({vertexShader:x1,fragmentShader:g1,uniforms:{depthColor:{value:this.texture},depthWidth:{value:Q.z},depthHeight:{value:Q.w}}});this.mesh=new C0(new V6(20,20),$)}}return this.mesh}reset(){this.texture=null,this.mesh=null}getDepthTexture(){return this.texture}}class SH extends w8{constructor(J,Q){super();let $=this,Z=null,W=1,H=null,Y="local-floor",X=1,K=null,U=null,G=null,q=null,E=null,F=null,k=new AH,M={},N=Q.getContextAttributes(),O=null,C=null,L=[],w=[],v=new PJ,_=null,T=new O0;T.viewport=new sJ;let x=new O0;x.viewport=new sJ;let z=[T,x],V=new T$,j=null,m=null;this.cameraAutoUpdate=!0,this.enabled=!1,this.isPresenting=!1,this.getController=function(d){let WJ=L[d];if(WJ===void 0)WJ=new O6,L[d]=WJ;return WJ.getTargetRaySpace()},this.getControllerGrip=function(d){let WJ=L[d];if(WJ===void 0)WJ=new O6,L[d]=WJ;return WJ.getGripSpace()},this.getHand=function(d){let WJ=L[d];if(WJ===void 0)WJ=new O6,L[d]=WJ;return WJ.getHandSpace()};function l(d){let WJ=w.indexOf(d.inputSource);if(WJ===-1)return;let MJ=L[WJ];if(MJ!==void 0)MJ.update(d.inputSource,d.frame,K||H),MJ.dispatchEvent({type:d.type,data:d.inputSource})}function c(){Z.removeEventListener("select",l),Z.removeEventListener("selectstart",l),Z.removeEventListener("selectend",l),Z.removeEventListener("squeeze",l),Z.removeEventListener("squeezestart",l),Z.removeEventListener("squeezeend",l),Z.removeEventListener("end",c),Z.removeEventListener("inputsourceschange",i);for(let d=0;d<L.length;d++){let WJ=w[d];if(WJ===null)continue;w[d]=null,L[d].disconnect(WJ)}j=null,m=null,k.reset();for(let d in M)delete M[d];J.setRenderTarget(O),E=null,q=null,G=null,Z=null,C=null,Y0.stop(),$.isPresenting=!1,J.setPixelRatio(_),J.setSize(v.width,v.height,!1),$.dispatchEvent({type:"sessionend"})}this.setFramebufferScaleFactor=function(d){if(W=d,$.isPresenting===!0)console.warn("THREE.WebXRManager: Cannot change framebuffer scale while presenting.")},this.setReferenceSpaceType=function(d){if(Y=d,$.isPresenting===!0)console.warn("THREE.WebXRManager: Cannot change reference space type while presenting.")},this.getReferenceSpace=function(){return K||H},this.setReferenceSpace=function(d){K=d},this.getBaseLayer=function(){return q!==null?q:E},this.getBinding=function(){return G},this.getFrame=function(){return F},this.getSession=function(){return Z},this.setSession=async function(d){if(Z=d,Z!==null){if(O=J.getRenderTarget(),Z.addEventListener("select",l),Z.addEventListener("selectstart",l),Z.addEventListener("selectend",l),Z.addEventListener("squeeze",l),Z.addEventListener("squeezestart",l),Z.addEventListener("squeezeend",l),Z.addEventListener("end",c),Z.addEventListener("inputsourceschange",i),N.xrCompatible!==!0)await Q.makeXRCompatible();if(_=J.getPixelRatio(),J.getSize(v),typeof XRWebGLBinding!=="undefined")G=new XRWebGLBinding(Z,Q);if(!(G!==null&&("createProjectionLayer"in XRWebGLBinding.prototype))){let MJ={antialias:N.antialias,alpha:!0,depth:N.depth,stencil:N.stencil,framebufferScaleFactor:W};E=new XRWebGLLayer(Z,Q,MJ),Z.updateRenderState({baseLayer:E}),J.setPixelRatio(1),J.setSize(E.framebufferWidth,E.framebufferHeight,!1),C=new _8(E.framebufferWidth,E.framebufferHeight,{format:U8,type:p8,colorSpace:J.outputColorSpace,stencilBuffer:N.stencil,resolveDepthBuffer:E.ignoreDepthValues===!1,resolveStencilBuffer:E.ignoreDepthValues===!1})}else{let MJ=null,GJ=null,RJ=null;if(N.depth)RJ=N.stencil?Q.DEPTH24_STENCIL8:Q.DEPTH_COMPONENT24,MJ=N.stencil?q6:N7,GJ=N.stencil?h9:f9;let uJ={colorFormat:Q.RGBA8,depthFormat:RJ,scaleFactor:W};q=G.createProjectionLayer(uJ),Z.updateRenderState({layers:[q]}),J.setPixelRatio(1),J.setSize(q.textureWidth,q.textureHeight,!1),C=new _8(q.textureWidth,q.textureHeight,{format:U8,type:p8,depthTexture:new y7(q.textureWidth,q.textureHeight,GJ,void 0,void 0,void 0,void 0,void 0,void 0,MJ),stencilBuffer:N.stencil,colorSpace:J.outputColorSpace,samples:N.antialias?4:0,resolveDepthBuffer:q.ignoreDepthValues===!1,resolveStencilBuffer:q.ignoreDepthValues===!1})}C.isXRRenderTarget=!0,this.setFoveation(X),K=null,H=await Z.requestReferenceSpace(Y),Y0.setContext(Z),Y0.start(),$.isPresenting=!0,$.dispatchEvent({type:"sessionstart"})}},this.getEnvironmentBlendMode=function(){if(Z!==null)return Z.environmentBlendMode},this.getDepthTexture=function(){return k.getDepthTexture()};function i(d){for(let WJ=0;WJ<d.removed.length;WJ++){let MJ=d.removed[WJ],GJ=w.indexOf(MJ);if(GJ>=0)w[GJ]=null,L[GJ].disconnect(MJ)}for(let WJ=0;WJ<d.added.length;WJ++){let MJ=d.added[WJ],GJ=w.indexOf(MJ);if(GJ===-1){for(let uJ=0;uJ<L.length;uJ++)if(uJ>=w.length){w.push(MJ),GJ=uJ;break}else if(w[uJ]===null){w[uJ]=MJ,GJ=uJ;break}if(GJ===-1)break}let RJ=L[GJ];if(RJ)RJ.connect(MJ)}}let u=new A,r=new A;function g(d,WJ,MJ){u.setFromMatrixPosition(WJ.matrixWorld),r.setFromMatrixPosition(MJ.matrixWorld);let GJ=u.distanceTo(r),RJ=WJ.projectionMatrix.elements,uJ=MJ.projectionMatrix.elements,cJ=RJ[14]/(RJ[10]-1),dJ=RJ[14]/(RJ[10]+1),I=(RJ[9]+1)/RJ[5],$0=(RJ[9]-1)/RJ[5],CJ=(RJ[8]-1)/RJ[0],iJ=(uJ[8]+1)/uJ[0],zJ=cJ*CJ,X0=cJ*iJ,DJ=GJ/(-CJ+iJ),_J=DJ*-CJ;if(WJ.matrixWorld.decompose(d.position,d.quaternion,d.scale),d.translateX(_J),d.translateZ(DJ),d.matrixWorld.compose(d.position,d.quaternion,d.scale),d.matrixWorldInverse.copy(d.matrixWorld).invert(),RJ[10]===-1)d.projectionMatrix.copy(WJ.projectionMatrix),d.projectionMatrixInverse.copy(WJ.projectionMatrixInverse);else{let V0=cJ+DJ,D0=dJ+DJ,N0=zJ-_J,B=X0+(GJ-_J),R=I*dJ/D0*V0,f=$0*dJ/D0*V0;d.projectionMatrix.makePerspective(N0,B,R,f,V0,D0),d.projectionMatrixInverse.copy(d.projectionMatrix).invert()}}function ZJ(d,WJ){if(WJ===null)d.matrixWorld.copy(d.matrix);else d.matrixWorld.multiplyMatrices(WJ.matrixWorld,d.matrix);d.matrixWorldInverse.copy(d.matrixWorld).invert()}this.updateCamera=function(d){if(Z===null)return;let{near:WJ,far:MJ}=d;if(k.texture!==null){if(k.depthNear>0)WJ=k.depthNear;if(k.depthFar>0)MJ=k.depthFar}if(V.near=x.near=T.near=WJ,V.far=x.far=T.far=MJ,j!==V.near||m!==V.far)Z.updateRenderState({depthNear:V.near,depthFar:V.far}),j=V.near,m=V.far;V.layers.mask=d.layers.mask|6,T.layers.mask=V.layers.mask&3,x.layers.mask=V.layers.mask&5;let GJ=d.parent,RJ=V.cameras;ZJ(V,GJ);for(let uJ=0;uJ<RJ.length;uJ++)ZJ(RJ[uJ],GJ);if(RJ.length===2)g(V,T,x);else V.projectionMatrix.copy(T.projectionMatrix);UJ(d,V,GJ)};function UJ(d,WJ,MJ){if(MJ===null)d.matrix.copy(WJ.matrixWorld);else d.matrix.copy(MJ.matrixWorld),d.matrix.invert(),d.matrix.multiply(WJ.matrixWorld);if(d.matrix.decompose(d.position,d.quaternion,d.scale),d.updateMatrixWorld(!0),d.projectionMatrix.copy(WJ.projectionMatrix),d.projectionMatrixInverse.copy(WJ.projectionMatrixInverse),d.isPerspectiveCamera)d.fov=Q9*2*Math.atan(1/d.projectionMatrix.elements[5]),d.zoom=1}this.getCamera=function(){return V},this.getFoveation=function(){if(q===null&&E===null)return;return X},this.setFoveation=function(d){if(X=d,q!==null)q.fixedFoveation=d;if(E!==null&&E.fixedFoveation!==void 0)E.fixedFoveation=d},this.hasDepthSensing=function(){return k.texture!==null},this.getDepthSensingMesh=function(){return k.getMesh(V)},this.getCameraTexture=function(d){return M[d]};let TJ=null;function mJ(d,WJ){if(U=WJ.getViewerPose(K||H),F=WJ,U!==null){let MJ=U.views;if(E!==null)J.setRenderTargetFramebuffer(C,E.framebuffer),J.setRenderTarget(C);let GJ=!1;if(MJ.length!==V.cameras.length)V.cameras.length=0,GJ=!0;for(let dJ=0;dJ<MJ.length;dJ++){let I=MJ[dJ],$0=null;if(E!==null)$0=E.getViewport(I);else{let iJ=G.getViewSubImage(q,I);if($0=iJ.viewport,dJ===0)J.setRenderTargetTextures(C,iJ.colorTexture,iJ.depthStencilTexture),J.setRenderTarget(C)}let CJ=z[dJ];if(CJ===void 0)CJ=new O0,CJ.layers.enable(dJ),CJ.viewport=new sJ,z[dJ]=CJ;if(CJ.matrix.fromArray(I.transform.matrix),CJ.matrix.decompose(CJ.position,CJ.quaternion,CJ.scale),CJ.projectionMatrix.fromArray(I.projectionMatrix),CJ.projectionMatrixInverse.copy(CJ.projectionMatrix).invert(),CJ.viewport.set($0.x,$0.y,$0.width,$0.height),dJ===0)V.matrix.copy(CJ.matrix),V.matrix.decompose(V.position,V.quaternion,V.scale);if(GJ===!0)V.cameras.push(CJ)}let RJ=Z.enabledFeatures;if(RJ&&RJ.includes("depth-sensing")&&Z.depthUsage=="gpu-optimized"&&G){let dJ=G.getDepthInformation(MJ[0]);if(dJ&&dJ.isValid&&dJ.texture)k.init(dJ,Z.renderState)}if(RJ&&RJ.includes("camera-access")){if(J.state.unbindTexture(),G)for(let dJ=0;dJ<MJ.length;dJ++){let I=MJ[dJ].camera;if(I){let $0=M[I];if(!$0)$0=new d$,M[I]=$0;let CJ=G.getCameraImage(I);$0.sourceTexture=CJ}}}}for(let MJ=0;MJ<L.length;MJ++){let GJ=w[MJ],RJ=L[MJ];if(GJ!==null&&RJ!==void 0)RJ.update(GJ,WJ,K||H)}if(TJ)TJ(d,WJ);if(WJ.detectedPlanes)$.dispatchEvent({type:"planesdetected",data:WJ});F=null}let Y0=new LH;Y0.setAnimationLoop(mJ),this.setAnimationLoop=function(d){TJ=d},this.dispose=function(){}}}var G9=new $8,p1=new vJ;function l1(J,Q){function $(N,O){if(N.matrixAutoUpdate===!0)N.updateMatrix();O.value.copy(N.matrix)}function Z(N,O){if(O.color.getRGB(N.fogColor.value,M$(J)),O.isFog)N.fogNear.value=O.near,N.fogFar.value=O.far;else if(O.isFogExp2)N.fogDensity.value=O.density}function W(N,O,C,L,w){if(O.isMeshBasicMaterial)H(N,O);else if(O.isMeshLambertMaterial)H(N,O);else if(O.isMeshToonMaterial)H(N,O),q(N,O);else if(O.isMeshPhongMaterial)H(N,O),G(N,O);else if(O.isMeshStandardMaterial){if(H(N,O),E(N,O),O.isMeshPhysicalMaterial)F(N,O,w)}else if(O.isMeshMatcapMaterial)H(N,O),k(N,O);else if(O.isMeshDepthMaterial)H(N,O);else if(O.isMeshDistanceMaterial)H(N,O),M(N,O);else if(O.isMeshNormalMaterial)H(N,O);else if(O.isLineBasicMaterial){if(Y(N,O),O.isLineDashedMaterial)X(N,O)}else if(O.isPointsMaterial)K(N,O,C,L);else if(O.isSpriteMaterial)U(N,O);else if(O.isShadowMaterial)N.color.value.copy(O.color),N.opacity.value=O.opacity;else if(O.isShaderMaterial)O.uniformsNeedUpdate=!1}function H(N,O){if(N.opacity.value=O.opacity,O.color)N.diffuse.value.copy(O.color);if(O.emissive)N.emissive.value.copy(O.emissive).multiplyScalar(O.emissiveIntensity);if(O.map)N.map.value=O.map,$(O.map,N.mapTransform);if(O.alphaMap)N.alphaMap.value=O.alphaMap,$(O.alphaMap,N.alphaMapTransform);if(O.bumpMap){if(N.bumpMap.value=O.bumpMap,$(O.bumpMap,N.bumpMapTransform),N.bumpScale.value=O.bumpScale,O.side===b0)N.bumpScale.value*=-1}if(O.normalMap){if(N.normalMap.value=O.normalMap,$(O.normalMap,N.normalMapTransform),N.normalScale.value.copy(O.normalScale),O.side===b0)N.normalScale.value.negate()}if(O.displacementMap)N.displacementMap.value=O.displacementMap,$(O.displacementMap,N.displacementMapTransform),N.displacementScale.value=O.displacementScale,N.displacementBias.value=O.displacementBias;if(O.emissiveMap)N.emissiveMap.value=O.emissiveMap,$(O.emissiveMap,N.emissiveMapTransform);if(O.specularMap)N.specularMap.value=O.specularMap,$(O.specularMap,N.specularMapTransform);if(O.alphaTest>0)N.alphaTest.value=O.alphaTest;let C=Q.get(O),L=C.envMap,w=C.envMapRotation;if(L){if(N.envMap.value=L,G9.copy(w),G9.x*=-1,G9.y*=-1,G9.z*=-1,L.isCubeTexture&&L.isRenderTargetTexture===!1)G9.y*=-1,G9.z*=-1;N.envMapRotation.value.setFromMatrix4(p1.makeRotationFromEuler(G9)),N.flipEnvMap.value=L.isCubeTexture&&L.isRenderTargetTexture===!1?-1:1,N.reflectivity.value=O.reflectivity,N.ior.value=O.ior,N.refractionRatio.value=O.refractionRatio}if(O.lightMap)N.lightMap.value=O.lightMap,N.lightMapIntensity.value=O.lightMapIntensity,$(O.lightMap,N.lightMapTransform);if(O.aoMap)N.aoMap.value=O.aoMap,N.aoMapIntensity.value=O.aoMapIntensity,$(O.aoMap,N.aoMapTransform)}function Y(N,O){if(N.diffuse.value.copy(O.color),N.opacity.value=O.opacity,O.map)N.map.value=O.map,$(O.map,N.mapTransform)}function X(N,O){N.dashSize.value=O.dashSize,N.totalSize.value=O.dashSize+O.gapSize,N.scale.value=O.scale}function K(N,O,C,L){if(N.diffuse.value.copy(O.color),N.opacity.value=O.opacity,N.size.value=O.size*C,N.scale.value=L*0.5,O.map)N.map.value=O.map,$(O.map,N.uvTransform);if(O.alphaMap)N.alphaMap.value=O.alphaMap,$(O.alphaMap,N.alphaMapTransform);if(O.alphaTest>0)N.alphaTest.value=O.alphaTest}function U(N,O){if(N.diffuse.value.copy(O.color),N.opacity.value=O.opacity,N.rotation.value=O.rotation,O.map)N.map.value=O.map,$(O.map,N.mapTransform);if(O.alphaMap)N.alphaMap.value=O.alphaMap,$(O.alphaMap,N.alphaMapTransform);if(O.alphaTest>0)N.alphaTest.value=O.alphaTest}function G(N,O){N.specular.value.copy(O.specular),N.shininess.value=Math.max(O.shininess,0.0001)}function q(N,O){if(O.gradientMap)N.gradientMap.value=O.gradientMap}function E(N,O){if(N.metalness.value=O.metalness,O.metalnessMap)N.metalnessMap.value=O.metalnessMap,$(O.metalnessMap,N.metalnessMapTransform);if(N.roughness.value=O.roughness,O.roughnessMap)N.roughnessMap.value=O.roughnessMap,$(O.roughnessMap,N.roughnessMapTransform);if(O.envMap)N.envMapIntensity.value=O.envMapIntensity}function F(N,O,C){if(N.ior.value=O.ior,O.sheen>0){if(N.sheenColor.value.copy(O.sheenColor).multiplyScalar(O.sheen),N.sheenRoughness.value=O.sheenRoughness,O.sheenColorMap)N.sheenColorMap.value=O.sheenColorMap,$(O.sheenColorMap,N.sheenColorMapTransform);if(O.sheenRoughnessMap)N.sheenRoughnessMap.value=O.sheenRoughnessMap,$(O.sheenRoughnessMap,N.sheenRoughnessMapTransform)}if(O.clearcoat>0){if(N.clearcoat.value=O.clearcoat,N.clearcoatRoughness.value=O.clearcoatRoughness,O.clearcoatMap)N.clearcoatMap.value=O.clearcoatMap,$(O.clearcoatMap,N.clearcoatMapTransform);if(O.clearcoatRoughnessMap)N.clearcoatRoughnessMap.value=O.clearcoatRoughnessMap,$(O.clearcoatRoughnessMap,N.clearcoatRoughnessMapTransform);if(O.clearcoatNormalMap){if(N.clearcoatNormalMap.value=O.clearcoatNormalMap,$(O.clearcoatNormalMap,N.clearcoatNormalMapTransform),N.clearcoatNormalScale.value.copy(O.clearcoatNormalScale),O.side===b0)N.clearcoatNormalScale.value.negate()}}if(O.dispersion>0)N.dispersion.value=O.dispersion;if(O.iridescence>0){if(N.iridescence.value=O.iridescence,N.iridescenceIOR.value=O.iridescenceIOR,N.iridescenceThicknessMinimum.value=O.iridescenceThicknessRange[0],N.iridescenceThicknessMaximum.value=O.iridescenceThicknessRange[1],O.iridescenceMap)N.iridescenceMap.value=O.iridescenceMap,$(O.iridescenceMap,N.iridescenceMapTransform);if(O.iridescenceThicknessMap)N.iridescenceThicknessMap.value=O.iridescenceThicknessMap,$(O.iridescenceThicknessMap,N.iridescenceThicknessMapTransform)}if(O.transmission>0){if(N.transmission.value=O.transmission,N.transmissionSamplerMap.value=C.texture,N.transmissionSamplerSize.value.set(C.width,C.height),O.transmissionMap)N.transmissionMap.value=O.transmissionMap,$(O.transmissionMap,N.transmissionMapTransform);if(N.thickness.value=O.thickness,O.thicknessMap)N.thicknessMap.value=O.thicknessMap,$(O.thicknessMap,N.thicknessMapTransform);N.attenuationDistance.value=O.attenuationDistance,N.attenuationColor.value.copy(O.attenuationColor)}if(O.anisotropy>0){if(N.anisotropyVector.value.set(O.anisotropy*Math.cos(O.anisotropyRotation),O.anisotropy*Math.sin(O.anisotropyRotation)),O.anisotropyMap)N.anisotropyMap.value=O.anisotropyMap,$(O.anisotropyMap,N.anisotropyMapTransform)}if(N.specularIntensity.value=O.specularIntensity,N.specularColor.value.copy(O.specularColor),O.specularColorMap)N.specularColorMap.value=O.specularColorMap,$(O.specularColorMap,N.specularColorMapTransform);if(O.specularIntensityMap)N.specularIntensityMap.value=O.specularIntensityMap,$(O.specularIntensityMap,N.specularIntensityMapTransform)}function k(N,O){if(O.matcap)N.matcap.value=O.matcap}function M(N,O){let C=Q.get(O).light;N.referencePosition.value.setFromMatrixPosition(C.matrixWorld),N.nearDistance.value=C.shadow.camera.near,N.farDistance.value=C.shadow.camera.far}return{refreshFogUniforms:Z,refreshMaterialUniforms:W}}function d1(J,Q,$,Z){let W={},H={},Y=[],X=J.getParameter(J.MAX_UNIFORM_BUFFER_BINDINGS);function K(C,L){let w=L.program;Z.uniformBlockBinding(C,w)}function U(C,L){let w=W[C.id];if(w===void 0)k(C),w=G(C),W[C.id]=w,C.addEventListener("dispose",N);let v=L.program;Z.updateUBOMapping(C,v);let _=Q.render.frame;if(H[C.id]!==_)E(C),H[C.id]=_}function G(C){let L=q();C.__bindingPointIndex=L;let w=J.createBuffer(),v=C.__size,_=C.usage;return J.bindBuffer(J.UNIFORM_BUFFER,w),J.bufferData(J.UNIFORM_BUFFER,v,_),J.bindBuffer(J.UNIFORM_BUFFER,null),J.bindBufferBase(J.UNIFORM_BUFFER,L,w),w}function q(){for(let C=0;C<X;C++)if(Y.indexOf(C)===-1)return Y.push(C),C;return console.error("THREE.WebGLRenderer: Maximum number of simultaneously usable uniforms groups reached."),0}function E(C){let L=W[C.id],w=C.uniforms,v=C.__cache;J.bindBuffer(J.UNIFORM_BUFFER,L);for(let _=0,T=w.length;_<T;_++){let x=Array.isArray(w[_])?w[_]:[w[_]];for(let z=0,V=x.length;z<V;z++){let j=x[z];if(F(j,_,z,v)===!0){let m=j.__offset,l=Array.isArray(j.value)?j.value:[j.value],c=0;for(let i=0;i<l.length;i++){let u=l[i],r=M(u);if(typeof u==="number"||typeof u==="boolean")j.__data[0]=u,J.bufferSubData(J.UNIFORM_BUFFER,m+c,j.__data);else if(u.isMatrix3)j.__data[0]=u.elements[0],j.__data[1]=u.elements[1],j.__data[2]=u.elements[2],j.__data[3]=0,j.__data[4]=u.elements[3],j.__data[5]=u.elements[4],j.__data[6]=u.elements[5],j.__data[7]=0,j.__data[8]=u.elements[6],j.__data[9]=u.elements[7],j.__data[10]=u.elements[8],j.__data[11]=0;else u.toArray(j.__data,c),c+=r.storage/Float32Array.BYTES_PER_ELEMENT}J.bufferSubData(J.UNIFORM_BUFFER,m,j.__data)}}}J.bindBuffer(J.UNIFORM_BUFFER,null)}function F(C,L,w,v){let _=C.value,T=L+"_"+w;if(v[T]===void 0){if(typeof _==="number"||typeof _==="boolean")v[T]=_;else v[T]=_.clone();return!0}else{let x=v[T];if(typeof _==="number"||typeof _==="boolean"){if(x!==_)return v[T]=_,!0}else if(x.equals(_)===!1)return x.copy(_),!0}return!1}function k(C){let L=C.uniforms,w=0,v=16;for(let T=0,x=L.length;T<x;T++){let z=Array.isArray(L[T])?L[T]:[L[T]];for(let V=0,j=z.length;V<j;V++){let m=z[V],l=Array.isArray(m.value)?m.value:[m.value];for(let c=0,i=l.length;c<i;c++){let u=l[c],r=M(u),g=w%v,ZJ=g%r.boundary,UJ=g+ZJ;if(w+=ZJ,UJ!==0&&v-UJ<r.storage)w+=v-UJ;m.__data=new Float32Array(r.storage/Float32Array.BYTES_PER_ELEMENT),m.__offset=w,w+=r.storage}}}let _=w%v;if(_>0)w+=v-_;return C.__size=w,C.__cache={},this}function M(C){let L={boundary:0,storage:0};if(typeof C==="number"||typeof C==="boolean")L.boundary=4,L.storage=4;else if(C.isVector2)L.boundary=8,L.storage=8;else if(C.isVector3||C.isColor)L.boundary=16,L.storage=12;else if(C.isVector4)L.boundary=16,L.storage=16;else if(C.isMatrix3)L.boundary=48,L.storage=48;else if(C.isMatrix4)L.boundary=64,L.storage=64;else if(C.isTexture)console.warn("THREE.WebGLRenderer: Texture samplers can not be part of an uniforms group.");else console.warn("THREE.WebGLRenderer: Unsupported uniform value type.",C);return L}function N(C){let L=C.target;L.removeEventListener("dispose",N);let w=Y.indexOf(L.__bindingPointIndex);Y.splice(w,1),J.deleteBuffer(W[L.id]),delete W[L.id],delete H[L.id]}function O(){for(let C in W)J.deleteBuffer(W[C]);Y=[],W={},H={}}return{bind:K,update:U,dispose:O}}class m${constructor(J={}){let{canvas:Q=pW(),context:$=null,depth:Z=!0,stencil:W=!1,alpha:H=!1,antialias:Y=!1,premultipliedAlpha:X=!0,preserveDrawingBuffer:K=!1,powerPreference:U="default",failIfMajorPerformanceCaveat:G=!1,reversedDepthBuffer:q=!1}=J;this.isWebGLRenderer=!0;let E;if($!==null){if(typeof WebGLRenderingContext!=="undefined"&&$ instanceof WebGLRenderingContext)throw new Error("THREE.WebGLRenderer: WebGL 1 is not supported since r163.");E=$.getContextAttributes().alpha}else E=H;let F=new Uint32Array(4),k=new Int32Array(4),M=null,N=null,O=[],C=[];this.domElement=Q,this.debug={checkShaderErrors:!0,onShaderError:null},this.autoClear=!0,this.autoClearColor=!0,this.autoClearDepth=!0,this.autoClearStencil=!0,this.sortObjects=!0,this.clippingPlanes=[],this.localClippingEnabled=!1,this.toneMapping=z8,this.toneMappingExposure=1,this.transmissionResolutionScale=1;let L=this,w=!1;this._outputColorSpace=d8;let v=0,_=0,T=null,x=-1,z=null,V=new sJ,j=new sJ,m=null,l=new jJ(0),c=0,i=Q.width,u=Q.height,r=1,g=null,ZJ=null,UJ=new sJ(0,0,i,u),TJ=new sJ(0,0,i,u),mJ=!1,Y0=new M6,d=!1,WJ=!1,MJ=new vJ,GJ=new A,RJ=new sJ,uJ={background:null,fog:null,environment:null,overrideMaterial:null,isScene:!0},cJ=!1;function dJ(){return T===null?r:1}let I=$;function $0(D,S){return Q.getContext(D,S)}try{let D={alpha:!0,depth:Z,stencil:W,antialias:Y,premultipliedAlpha:X,preserveDrawingBuffer:K,powerPreference:U,failIfMajorPerformanceCaveat:G};if("setAttribute"in Q)Q.setAttribute("data-engine",`three.js r${dZ}`);if(Q.addEventListener("webglcontextlost",HJ,!1),Q.addEventListener("webglcontextrestored",QJ,!1),Q.addEventListener("webglcontextcreationerror",NJ,!1),I===null){if(I=$0("webgl2",D),I===null)if($0("webgl2"))throw new Error("Error creating WebGL context with your selected attributes.");else throw new Error("Error creating WebGL context.")}}catch(D){throw console.error("THREE.WebGLRenderer: "+D.message),D}let CJ,iJ,zJ,X0,DJ,_J,V0,D0,N0,B,R,f,n,o,p,EJ,JJ,kJ,AJ,e,XJ,LJ,VJ,KJ;function bJ(){if(CJ=new YG(I),CJ.init(),LJ=new b1(I,CJ),iJ=new eU(I,CJ,J,LJ),zJ=new f1(I,CJ),iJ.reversedDepthBuffer&&q)zJ.buffers.depth.setReversed(!0);X0=new UG(I),DJ=new z1,_J=new h1(I,CJ,zJ,DJ,iJ,LJ,X0),V0=new QG(L),D0=new HG(L),N0=new FX(I),VJ=new rU(I,N0),B=new XG(I,N0,X0,VJ),R=new qG(I,B,N0,X0),AJ=new GG(I,iJ,_J),EJ=new JG(DJ),f=new V1(L,V0,D0,CJ,iJ,VJ,EJ),n=new l1(L,DJ),o=new C1,p=new A1(CJ),kJ=new aU(L,V0,D0,zJ,R,E,X),JJ=new y1(L,R,iJ),KJ=new d1(I,X0,iJ,zJ),e=new tU(I,CJ,X0),XJ=new KG(I,CJ,X0),X0.programs=f.programs,L.capabilities=iJ,L.extensions=CJ,L.properties=DJ,L.renderLists=o,L.shadowMap=JJ,L.state=zJ,L.info=X0}bJ();let P=new SH(L,I);this.xr=P,this.getContext=function(){return I},this.getContextAttributes=function(){return I.getContextAttributes()},this.forceContextLoss=function(){let D=CJ.get("WEBGL_lose_context");if(D)D.loseContext()},this.forceContextRestore=function(){let D=CJ.get("WEBGL_lose_context");if(D)D.restoreContext()},this.getPixelRatio=function(){return r},this.setPixelRatio=function(D){if(D===void 0)return;r=D,this.setSize(i,u,!1)},this.getSize=function(D){return D.set(i,u)},this.setSize=function(D,S,h=!0){if(P.isPresenting){console.warn("THREE.WebGLRenderer: Can't change size while VR device is presenting.");return}if(i=D,u=S,Q.width=Math.floor(D*r),Q.height=Math.floor(S*r),h===!0)Q.style.width=D+"px",Q.style.height=S+"px";this.setViewport(0,0,D,S)},this.getDrawingBufferSize=function(D){return D.set(i*r,u*r).floor()},this.setDrawingBufferSize=function(D,S,h){i=D,u=S,r=h,Q.width=Math.floor(D*h),Q.height=Math.floor(S*h),this.setViewport(0,0,D,S)},this.getCurrentViewport=function(D){return D.copy(V)},this.getViewport=function(D){return D.copy(UJ)},this.setViewport=function(D,S,h,b){if(D.isVector4)UJ.set(D.x,D.y,D.z,D.w);else UJ.set(D,S,h,b);zJ.viewport(V.copy(UJ).multiplyScalar(r).round())},this.getScissor=function(D){return D.copy(TJ)},this.setScissor=function(D,S,h,b){if(D.isVector4)TJ.set(D.x,D.y,D.z,D.w);else TJ.set(D,S,h,b);zJ.scissor(j.copy(TJ).multiplyScalar(r).round())},this.getScissorTest=function(){return mJ},this.setScissorTest=function(D){zJ.setScissorTest(mJ=D)},this.setOpaqueSort=function(D){g=D},this.setTransparentSort=function(D){ZJ=D},this.getClearColor=function(D){return D.copy(kJ.getClearColor())},this.setClearColor=function(){kJ.setClearColor(...arguments)},this.getClearAlpha=function(){return kJ.getClearAlpha()},this.setClearAlpha=function(){kJ.setClearAlpha(...arguments)},this.clear=function(D=!0,S=!0,h=!0){let b=0;if(D){let y=!1;if(T!==null){let t=T.texture.format;y=t===vQ||t===yQ||t===jQ}if(y){let t=T.texture.type,YJ=t===p8||t===f9||t===U6||t===h9||t===AQ||t===SQ,OJ=kJ.getClearColor(),qJ=kJ.getClearAlpha(),IJ=OJ.r,SJ=OJ.g,BJ=OJ.b;if(YJ)F[0]=IJ,F[1]=SJ,F[2]=BJ,F[3]=qJ,I.clearBufferuiv(I.COLOR,0,F);else k[0]=IJ,k[1]=SJ,k[2]=BJ,k[3]=qJ,I.clearBufferiv(I.COLOR,0,k)}else b|=I.COLOR_BUFFER_BIT}if(S)b|=I.DEPTH_BUFFER_BIT;if(h)b|=I.STENCIL_BUFFER_BIT,this.state.buffers.stencil.setMask(4294967295);I.clear(b)},this.clearColor=function(){this.clear(!0,!1,!1)},this.clearDepth=function(){this.clear(!1,!0,!1)},this.clearStencil=function(){this.clear(!1,!1,!0)},this.dispose=function(){Q.removeEventListener("webglcontextlost",HJ,!1),Q.removeEventListener("webglcontextrestored",QJ,!1),Q.removeEventListener("webglcontextcreationerror",NJ,!1),kJ.dispose(),o.dispose(),p.dispose(),DJ.dispose(),V0.dispose(),D0.dispose(),R.dispose(),VJ.dispose(),KJ.dispose(),f.dispose(),P.dispose(),P.removeEventListener("sessionstart",W8),P.removeEventListener("sessionend",H8),i8.stop()};function HJ(D){D.preventDefault(),console.log("THREE.WebGLRenderer: Context Lost."),w=!0}function QJ(){console.log("THREE.WebGLRenderer: Context Restored."),w=!1;let D=X0.autoReset,S=JJ.enabled,h=JJ.autoUpdate,b=JJ.needsUpdate,y=JJ.type;bJ(),X0.autoReset=D,JJ.enabled=S,JJ.autoUpdate=h,JJ.needsUpdate=b,JJ.type=y}function NJ(D){console.error("THREE.WebGLRenderer: A WebGL context could not be created. Reason: ",D.statusMessage)}function a(D){let S=D.target;S.removeEventListener("dispose",a),s(S)}function s(D){FJ(D),DJ.remove(D)}function FJ(D){let S=DJ.get(D).programs;if(S!==void 0){if(S.forEach(function(h){f.releaseProgram(h)}),D.isShaderMaterial)f.releaseShaderCache(D)}}this.renderBufferDirect=function(D,S,h,b,y,t){if(S===null)S=uJ;let YJ=y.isMesh&&y.matrixWorld.determinant()<0,OJ=GY(D,S,h,b,y);zJ.setMaterial(b,YJ);let qJ=h.index,IJ=1;if(b.wireframe===!0){if(qJ=B.getWireframeAttribute(h),qJ===void 0)return;IJ=2}let SJ=h.drawRange,BJ=h.attributes.position,pJ=SJ.start*IJ,tJ=(SJ.start+SJ.count)*IJ;if(t!==null)pJ=Math.max(pJ,t.start*IJ),tJ=Math.min(tJ,(t.start+t.count)*IJ);if(qJ!==null)pJ=Math.max(pJ,0),tJ=Math.min(tJ,qJ.count);else if(BJ!==void 0&&BJ!==null)pJ=Math.max(pJ,0),tJ=Math.min(tJ,BJ.count);let G0=tJ-pJ;if(G0<0||G0===1/0)return;VJ.setup(y,b,OJ,h,qJ);let H0,Q0=e;if(qJ!==null)H0=N0.get(qJ),Q0=XJ,Q0.setIndex(H0);if(y.isMesh)if(b.wireframe===!0)zJ.setLineWidth(b.wireframeLinewidth*dJ()),Q0.setMode(I.LINES);else Q0.setMode(I.TRIANGLES);else if(y.isLine){let wJ=b.linewidth;if(wJ===void 0)wJ=1;if(zJ.setLineWidth(wJ*dJ()),y.isLineSegments)Q0.setMode(I.LINES);else if(y.isLineLoop)Q0.setMode(I.LINE_LOOP);else Q0.setMode(I.LINE_STRIP)}else if(y.isPoints)Q0.setMode(I.POINTS);else if(y.isSprite)Q0.setMode(I.TRIANGLES);if(y.isBatchedMesh)if(y._multiDrawInstances!==null)$9("THREE.WebGLRenderer: renderMultiDrawInstances has been deprecated and will be removed in r184. Append to renderMultiDraw arguments and use indirection."),Q0.renderMultiDrawInstances(y._multiDrawStarts,y._multiDrawCounts,y._multiDrawCount,y._multiDrawInstances);else if(!CJ.get("WEBGL_multi_draw")){let{_multiDrawStarts:wJ,_multiDrawCounts:K0,_multiDrawCount:nJ}=y,y0=qJ?N0.get(qJ).bytesPerElement:1,O9=DJ.get(b).currentProgram.getUniforms();for(let v0=0;v0<nJ;v0++)O9.setValue(I,"_gl_DrawID",v0),Q0.render(wJ[v0]/y0,K0[v0])}else Q0.renderMultiDraw(y._multiDrawStarts,y._multiDrawCounts,y._multiDrawCount);else if(y.isInstancedMesh)Q0.renderInstances(pJ,G0,y.count);else if(h.isInstancedBufferGeometry){let wJ=h._maxInstanceCount!==void 0?h._maxInstanceCount:1/0,K0=Math.min(h.instanceCount,wJ);Q0.renderInstances(pJ,G0,K0)}else Q0.render(pJ,G0)};function yJ(D,S,h){if(D.transparent===!0&&D.side===o0&&D.forceSinglePass===!1)D.side=b0,D.needsUpdate=!0,P6(D,S,h),D.side=x8,D.needsUpdate=!0,P6(D,S,h),D.side=o0;else P6(D,S,h)}this.compile=function(D,S,h=null){if(h===null)h=D;if(N=p.get(h),N.init(S),C.push(N),h.traverseVisible(function(y){if(y.isLight&&y.layers.test(S.layers)){if(N.pushLight(y),y.castShadow)N.pushShadow(y)}}),D!==h)D.traverseVisible(function(y){if(y.isLight&&y.layers.test(S.layers)){if(N.pushLight(y),y.castShadow)N.pushShadow(y)}});N.setupLights();let b=new Set;return D.traverse(function(y){if(!(y.isMesh||y.isPoints||y.isLine||y.isSprite))return;let t=y.material;if(t)if(Array.isArray(t))for(let YJ=0;YJ<t.length;YJ++){let OJ=t[YJ];yJ(OJ,h,y),b.add(OJ)}else yJ(t,h,y),b.add(t)}),N=C.pop(),b},this.compileAsync=function(D,S,h=null){let b=this.compile(D,S,h);return new Promise((y)=>{function t(){if(b.forEach(function(YJ){if(DJ.get(YJ).currentProgram.isReady())b.delete(YJ)}),b.size===0){y(D);return}setTimeout(t,10)}if(CJ.get("KHR_parallel_shader_compile")!==null)t();else setTimeout(t,10)})};let J0=null;function rJ(D){if(J0)J0(D)}function W8(){i8.stop()}function H8(){i8.start()}let i8=new LH;if(i8.setAnimationLoop(rJ),typeof self!=="undefined")i8.setContext(self);this.setAnimationLoop=function(D){J0=D,P.setAnimationLoop(D),D===null?i8.stop():i8.start()},P.addEventListener("sessionstart",W8),P.addEventListener("sessionend",H8),this.render=function(D,S){if(S!==void 0&&S.isCamera!==!0){console.error("THREE.WebGLRenderer.render: camera is not an instance of THREE.Camera.");return}if(w===!0)return;if(D.matrixWorldAutoUpdate===!0)D.updateMatrixWorld();if(S.parent===null&&S.matrixWorldAutoUpdate===!0)S.updateMatrixWorld();if(P.enabled===!0&&P.isPresenting===!0){if(P.cameraAutoUpdate===!0)P.updateCamera(S);S=P.getCamera()}if(D.isScene===!0)D.onBeforeRender(L,D,S,T);if(N=p.get(D,C.length),N.init(S),C.push(N),MJ.multiplyMatrices(S.projectionMatrix,S.matrixWorldInverse),Y0.setFromProjectionMatrix(MJ,E$,S.reversedDepth),WJ=this.localClippingEnabled,d=EJ.init(this.clippingPlanes,WJ),M=o.get(D,O.length),M.init(),O.push(M),P.enabled===!0&&P.isPresenting===!0){let t=L.xr.getDepthSensingMesh();if(t!==null)o7(t,S,-1/0,L.sortObjects)}if(o7(D,S,0,L.sortObjects),M.finish(),L.sortObjects===!0)M.sort(g,ZJ);if(cJ=P.enabled===!1||P.isPresenting===!1||P.hasDepthSensing()===!1,cJ)kJ.addToRenderList(M,D);if(this.info.render.frame++,d===!0)EJ.beginShadows();let h=N.state.shadowsArray;if(JJ.render(h,D,S),d===!0)EJ.endShadows();if(this.info.autoReset===!0)this.info.reset();let{opaque:b,transmissive:y}=M;if(N.setupLights(),S.isArrayCamera){let t=S.cameras;if(y.length>0)for(let YJ=0,OJ=t.length;YJ<OJ;YJ++){let qJ=t[YJ];$Z(b,y,D,qJ)}if(cJ)kJ.render(D);for(let YJ=0,OJ=t.length;YJ<OJ;YJ++){let qJ=t[YJ];QZ(M,D,qJ,qJ.viewport)}}else{if(y.length>0)$Z(b,y,D,S);if(cJ)kJ.render(D);QZ(M,D,S)}if(T!==null&&_===0)_J.updateMultisampleRenderTarget(T),_J.updateRenderTargetMipmap(T);if(D.isScene===!0)D.onAfterRender(L,D,S);if(VJ.resetDefaultState(),x=-1,z=null,C.pop(),C.length>0){if(N=C[C.length-1],d===!0)EJ.setGlobalState(L.clippingPlanes,N.state.camera)}else N=null;if(O.pop(),O.length>0)M=O[O.length-1];else M=null};function o7(D,S,h,b){if(D.visible===!1)return;if(D.layers.test(S.layers)){if(D.isGroup)h=D.renderOrder;else if(D.isLOD){if(D.autoUpdate===!0)D.update(S)}else if(D.isLight){if(N.pushLight(D),D.castShadow)N.pushShadow(D)}else if(D.isSprite){if(!D.frustumCulled||Y0.intersectsSprite(D)){if(b)RJ.setFromMatrixPosition(D.matrixWorld).applyMatrix4(MJ);let YJ=R.update(D),OJ=D.material;if(OJ.visible)M.push(D,YJ,OJ,h,RJ.z,null)}}else if(D.isMesh||D.isLine||D.isPoints){if(!D.frustumCulled||Y0.intersectsObject(D)){let YJ=R.update(D),OJ=D.material;if(b){if(D.boundingSphere!==void 0){if(D.boundingSphere===null)D.computeBoundingSphere();RJ.copy(D.boundingSphere.center)}else{if(YJ.boundingSphere===null)YJ.computeBoundingSphere();RJ.copy(YJ.boundingSphere.center)}RJ.applyMatrix4(D.matrixWorld).applyMatrix4(MJ)}if(Array.isArray(OJ)){let qJ=YJ.groups;for(let IJ=0,SJ=qJ.length;IJ<SJ;IJ++){let BJ=qJ[IJ],pJ=OJ[BJ.materialIndex];if(pJ&&pJ.visible)M.push(D,YJ,pJ,h,RJ.z,BJ)}}else if(OJ.visible)M.push(D,YJ,OJ,h,RJ.z,null)}}}let t=D.children;for(let YJ=0,OJ=t.length;YJ<OJ;YJ++)o7(t[YJ],S,h,b)}function QZ(D,S,h,b){let{opaque:y,transmissive:t,transparent:YJ}=D;if(N.setupLightsView(h),d===!0)EJ.setGlobalState(L.clippingPlanes,h);if(b)zJ.viewport(V.copy(b));if(y.length>0)I6(y,S,h);if(t.length>0)I6(t,S,h);if(YJ.length>0)I6(YJ,S,h);zJ.buffers.depth.setTest(!0),zJ.buffers.depth.setMask(!0),zJ.buffers.color.setMask(!0),zJ.setPolygonOffset(!1)}function $Z(D,S,h,b){if((h.isScene===!0?h.overrideMaterial:null)!==null)return;if(N.state.transmissionRenderTarget[b.id]===void 0)N.state.transmissionRenderTarget[b.id]=new _8(1,1,{generateMipmaps:!0,type:CJ.has("EXT_color_buffer_half_float")||CJ.has("EXT_color_buffer_float")?G6:p8,minFilter:C8,samples:4,stencilBuffer:W,resolveDepthBuffer:!1,resolveStencilBuffer:!1,colorSpace:lJ.workingColorSpace});let t=N.state.transmissionRenderTarget[b.id],YJ=b.viewport||V;t.setSize(YJ.z*L.transmissionResolutionScale,YJ.w*L.transmissionResolutionScale);let OJ=L.getRenderTarget(),qJ=L.getActiveCubeFace(),IJ=L.getActiveMipmapLevel();if(L.setRenderTarget(t),L.getClearColor(l),c=L.getClearAlpha(),c<1)L.setClearColor(16777215,0.5);if(L.clear(),cJ)kJ.render(h);let SJ=L.toneMapping;L.toneMapping=z8;let BJ=b.viewport;if(b.viewport!==void 0)b.viewport=void 0;if(N.setupLightsView(b),d===!0)EJ.setGlobalState(L.clippingPlanes,b);if(I6(D,h,b),_J.updateMultisampleRenderTarget(t),_J.updateRenderTargetMipmap(t),CJ.has("WEBGL_multisampled_render_to_texture")===!1){let pJ=!1;for(let tJ=0,G0=S.length;tJ<G0;tJ++){let H0=S[tJ],Q0=H0.object,wJ=H0.geometry,K0=H0.material,nJ=H0.group;if(K0.side===o0&&Q0.layers.test(b.layers)){let y0=K0.side;K0.side=b0,K0.needsUpdate=!0,ZZ(Q0,h,b,wJ,K0,nJ),K0.side=y0,K0.needsUpdate=!0,pJ=!0}}if(pJ===!0)_J.updateMultisampleRenderTarget(t),_J.updateRenderTargetMipmap(t)}if(L.setRenderTarget(OJ,qJ,IJ),L.setClearColor(l,c),BJ!==void 0)b.viewport=BJ;L.toneMapping=SJ}function I6(D,S,h){let b=S.isScene===!0?S.overrideMaterial:null;for(let y=0,t=D.length;y<t;y++){let YJ=D[y],OJ=YJ.object,qJ=YJ.geometry,IJ=YJ.group,SJ=YJ.material;if(SJ.allowOverride===!0&&b!==null)SJ=b;if(OJ.layers.test(h.layers))ZZ(OJ,S,h,qJ,SJ,IJ)}}function ZZ(D,S,h,b,y,t){if(D.onBeforeRender(L,S,h,b,y,t),D.modelViewMatrix.multiplyMatrices(h.matrixWorldInverse,D.matrixWorld),D.normalMatrix.getNormalMatrix(D.modelViewMatrix),y.onBeforeRender(L,S,h,b,D,t),y.transparent===!0&&y.side===o0&&y.forceSinglePass===!1)y.side=b0,y.needsUpdate=!0,L.renderBufferDirect(h,S,b,y,D,t),y.side=x8,y.needsUpdate=!0,L.renderBufferDirect(h,S,b,y,D,t),y.side=o0;else L.renderBufferDirect(h,S,b,y,D,t);D.onAfterRender(L,S,h,b,y,t)}function P6(D,S,h){if(S.isScene!==!0)S=uJ;let b=DJ.get(D),y=N.state.lights,t=N.state.shadowsArray,YJ=y.state.version,OJ=f.getParameters(D,y.state,t,S,h),qJ=f.getProgramCacheKey(OJ),IJ=b.programs;if(b.environment=D.isMeshStandardMaterial?S.environment:null,b.fog=S.fog,b.envMap=(D.isMeshStandardMaterial?D0:V0).get(D.envMap||b.environment),b.envMapRotation=b.environment!==null&&D.envMap===null?S.environmentRotation:D.envMapRotation,IJ===void 0)D.addEventListener("dispose",a),IJ=new Map,b.programs=IJ;let SJ=IJ.get(qJ);if(SJ!==void 0){if(b.currentProgram===SJ&&b.lightsStateVersion===YJ)return HZ(D,OJ),SJ}else OJ.uniforms=f.getUniforms(D),D.onBeforeCompile(OJ,L),SJ=f.acquireProgram(OJ,qJ),IJ.set(qJ,SJ),b.uniforms=OJ.uniforms;let BJ=b.uniforms;if(!D.isShaderMaterial&&!D.isRawShaderMaterial||D.clipping===!0)BJ.clippingPlanes=EJ.uniform;if(HZ(D,OJ),b.needsLights=EY(D),b.lightsStateVersion=YJ,b.needsLights)BJ.ambientLightColor.value=y.state.ambient,BJ.lightProbe.value=y.state.probe,BJ.directionalLights.value=y.state.directional,BJ.directionalLightShadows.value=y.state.directionalShadow,BJ.spotLights.value=y.state.spot,BJ.spotLightShadows.value=y.state.spotShadow,BJ.rectAreaLights.value=y.state.rectArea,BJ.ltc_1.value=y.state.rectAreaLTC1,BJ.ltc_2.value=y.state.rectAreaLTC2,BJ.pointLights.value=y.state.point,BJ.pointLightShadows.value=y.state.pointShadow,BJ.hemisphereLights.value=y.state.hemi,BJ.directionalShadowMap.value=y.state.directionalShadowMap,BJ.directionalShadowMatrix.value=y.state.directionalShadowMatrix,BJ.spotShadowMap.value=y.state.spotShadowMap,BJ.spotLightMatrix.value=y.state.spotLightMatrix,BJ.spotLightMap.value=y.state.spotLightMap,BJ.pointShadowMap.value=y.state.pointShadowMap,BJ.pointShadowMatrix.value=y.state.pointShadowMatrix;return b.currentProgram=SJ,b.uniformsList=null,SJ}function WZ(D){if(D.uniformsList===null){let S=D.currentProgram.getUniforms();D.uniformsList=w6.seqWithValue(S.seq,D.uniforms)}return D.uniformsList}function HZ(D,S){let h=DJ.get(D);h.outputColorSpace=S.outputColorSpace,h.batching=S.batching,h.batchingColor=S.batchingColor,h.instancing=S.instancing,h.instancingColor=S.instancingColor,h.instancingMorph=S.instancingMorph,h.skinning=S.skinning,h.morphTargets=S.morphTargets,h.morphNormals=S.morphNormals,h.morphColors=S.morphColors,h.morphTargetsCount=S.morphTargetsCount,h.numClippingPlanes=S.numClippingPlanes,h.numIntersection=S.numClipIntersection,h.vertexAlphas=S.vertexAlphas,h.vertexTangents=S.vertexTangents,h.toneMapping=S.toneMapping}function GY(D,S,h,b,y){if(S.isScene!==!0)S=uJ;_J.resetTextureUnits();let t=S.fog,YJ=b.isMeshStandardMaterial?S.environment:null,OJ=T===null?L.outputColorSpace:T.isXRRenderTarget===!0?T.texture.colorSpace:P0,qJ=(b.isMeshStandardMaterial?D0:V0).get(b.envMap||YJ),IJ=b.vertexColors===!0&&!!h.attributes.color&&h.attributes.color.itemSize===4,SJ=!!h.attributes.tangent&&(!!b.normalMap||b.anisotropy>0),BJ=!!h.morphAttributes.position,pJ=!!h.morphAttributes.normal,tJ=!!h.morphAttributes.color,G0=z8;if(b.toneMapped){if(T===null||T.isXRRenderTarget===!0)G0=L.toneMapping}let H0=h.morphAttributes.position||h.morphAttributes.normal||h.morphAttributes.color,Q0=H0!==void 0?H0.length:0,wJ=DJ.get(b),K0=N.state.lights;if(d===!0){if(WJ===!0||D!==z){let _0=D===z&&b.id===x;EJ.setState(b,D,_0)}}let nJ=!1;if(b.version===wJ.__version){if(wJ.needsLights&&wJ.lightsStateVersion!==K0.state.version)nJ=!0;else if(wJ.outputColorSpace!==OJ)nJ=!0;else if(y.isBatchedMesh&&wJ.batching===!1)nJ=!0;else if(!y.isBatchedMesh&&wJ.batching===!0)nJ=!0;else if(y.isBatchedMesh&&wJ.batchingColor===!0&&y.colorTexture===null)nJ=!0;else if(y.isBatchedMesh&&wJ.batchingColor===!1&&y.colorTexture!==null)nJ=!0;else if(y.isInstancedMesh&&wJ.instancing===!1)nJ=!0;else if(!y.isInstancedMesh&&wJ.instancing===!0)nJ=!0;else if(y.isSkinnedMesh&&wJ.skinning===!1)nJ=!0;else if(!y.isSkinnedMesh&&wJ.skinning===!0)nJ=!0;else if(y.isInstancedMesh&&wJ.instancingColor===!0&&y.instanceColor===null)nJ=!0;else if(y.isInstancedMesh&&wJ.instancingColor===!1&&y.instanceColor!==null)nJ=!0;else if(y.isInstancedMesh&&wJ.instancingMorph===!0&&y.morphTexture===null)nJ=!0;else if(y.isInstancedMesh&&wJ.instancingMorph===!1&&y.morphTexture!==null)nJ=!0;else if(wJ.envMap!==qJ)nJ=!0;else if(b.fog===!0&&wJ.fog!==t)nJ=!0;else if(wJ.numClippingPlanes!==void 0&&(wJ.numClippingPlanes!==EJ.numPlanes||wJ.numIntersection!==EJ.numIntersection))nJ=!0;else if(wJ.vertexAlphas!==IJ)nJ=!0;else if(wJ.vertexTangents!==SJ)nJ=!0;else if(wJ.morphTargets!==BJ)nJ=!0;else if(wJ.morphNormals!==pJ)nJ=!0;else if(wJ.morphColors!==tJ)nJ=!0;else if(wJ.toneMapping!==G0)nJ=!0;else if(wJ.morphTargetsCount!==Q0)nJ=!0}else nJ=!0,wJ.__version=b.version;let y0=wJ.currentProgram;if(nJ===!0)y0=P6(b,S,y);let O9=!1,v0=!1,i9=!1,U0=y0.getUniforms(),m0=wJ.uniforms;if(zJ.useProgram(y0.program))O9=!0,v0=!0,i9=!0;if(b.id!==x)x=b.id,v0=!0;if(O9||z!==D){if(zJ.buffers.depth.getReversed()&&D.reversedDepth!==!0)D._reversedDepth=!0,D.updateProjectionMatrix();U0.setValue(I,"projectionMatrix",D.projectionMatrix),U0.setValue(I,"viewMatrix",D.matrixWorldInverse);let T0=U0.map.cameraPosition;if(T0!==void 0)T0.setValue(I,GJ.setFromMatrixPosition(D.matrixWorld));if(iJ.logarithmicDepthBuffer)U0.setValue(I,"logDepthBufFC",2/(Math.log(D.far+1)/Math.LN2));if(b.isMeshPhongMaterial||b.isMeshToonMaterial||b.isMeshLambertMaterial||b.isMeshBasicMaterial||b.isMeshStandardMaterial||b.isShaderMaterial)U0.setValue(I,"isOrthographic",D.isOrthographicCamera===!0);if(z!==D)z=D,v0=!0,i9=!0}if(y.isSkinnedMesh){U0.setOptional(I,y,"bindMatrix"),U0.setOptional(I,y,"bindMatrixInverse");let _0=y.skeleton;if(_0){if(_0.boneTexture===null)_0.computeBoneTexture();U0.setValue(I,"boneTexture",_0.boneTexture,_J)}}if(y.isBatchedMesh){if(U0.setOptional(I,y,"batchingTexture"),U0.setValue(I,"batchingTexture",y._matricesTexture,_J),U0.setOptional(I,y,"batchingIdTexture"),U0.setValue(I,"batchingIdTexture",y._indirectTexture,_J),U0.setOptional(I,y,"batchingColorTexture"),y._colorsTexture!==null)U0.setValue(I,"batchingColorTexture",y._colorsTexture,_J)}let u0=h.morphAttributes;if(u0.position!==void 0||u0.normal!==void 0||u0.color!==void 0)AJ.update(y,h,y0);if(v0||wJ.receiveShadow!==y.receiveShadow)wJ.receiveShadow=y.receiveShadow,U0.setValue(I,"receiveShadow",y.receiveShadow);if(b.isMeshGouraudMaterial&&b.envMap!==null)m0.envMap.value=qJ,m0.flipEnvMap.value=qJ.isCubeTexture&&qJ.isRenderTargetTexture===!1?-1:1;if(b.isMeshStandardMaterial&&b.envMap===null&&S.environment!==null)m0.envMapIntensity.value=S.environmentIntensity;if(v0){if(U0.setValue(I,"toneMappingExposure",L.toneMappingExposure),wJ.needsLights)qY(m0,i9);if(t&&b.fog===!0)n.refreshFogUniforms(m0,t);n.refreshMaterialUniforms(m0,b,r,u,N.state.transmissionRenderTarget[D.id]),w6.upload(I,WZ(wJ),m0,_J)}if(b.isShaderMaterial&&b.uniformsNeedUpdate===!0)w6.upload(I,WZ(wJ),m0,_J),b.uniformsNeedUpdate=!1;if(b.isSpriteMaterial)U0.setValue(I,"center",y.center);if(U0.setValue(I,"modelViewMatrix",y.modelViewMatrix),U0.setValue(I,"normalMatrix",y.normalMatrix),U0.setValue(I,"modelMatrix",y.matrixWorld),b.isShaderMaterial||b.isRawShaderMaterial){let _0=b.uniformsGroups;for(let T0=0,i7=_0.length;T0<i7;T0++){let a8=_0[T0];KJ.update(a8,y0),KJ.bind(a8,y0)}}return y0}function qY(D,S){D.ambientLightColor.needsUpdate=S,D.lightProbe.needsUpdate=S,D.directionalLights.needsUpdate=S,D.directionalLightShadows.needsUpdate=S,D.pointLights.needsUpdate=S,D.pointLightShadows.needsUpdate=S,D.spotLights.needsUpdate=S,D.spotLightShadows.needsUpdate=S,D.rectAreaLights.needsUpdate=S,D.hemisphereLights.needsUpdate=S}function EY(D){return D.isMeshLambertMaterial||D.isMeshToonMaterial||D.isMeshPhongMaterial||D.isMeshStandardMaterial||D.isShadowMaterial||D.isShaderMaterial&&D.lights===!0}this.getActiveCubeFace=function(){return v},this.getActiveMipmapLevel=function(){return _},this.getRenderTarget=function(){return T},this.setRenderTargetTextures=function(D,S,h){let b=DJ.get(D);if(b.__autoAllocateDepthBuffer=D.resolveDepthBuffer===!1,b.__autoAllocateDepthBuffer===!1)b.__useRenderToTexture=!1;DJ.get(D.texture).__webglTexture=S,DJ.get(D.depthTexture).__webglTexture=b.__autoAllocateDepthBuffer?void 0:h,b.__hasExternalTextures=!0},this.setRenderTargetFramebuffer=function(D,S){let h=DJ.get(D);h.__webglFramebuffer=S,h.__useDefaultFramebuffer=S===void 0};let NY=I.createFramebuffer();this.setRenderTarget=function(D,S=0,h=0){T=D,v=S,_=h;let b=!0,y=null,t=!1,YJ=!1;if(D){let qJ=DJ.get(D);if(qJ.__useDefaultFramebuffer!==void 0)zJ.bindFramebuffer(I.FRAMEBUFFER,null),b=!1;else if(qJ.__webglFramebuffer===void 0)_J.setupRenderTarget(D);else if(qJ.__hasExternalTextures)_J.rebindTextures(D,DJ.get(D.texture).__webglTexture,DJ.get(D.depthTexture).__webglTexture);else if(D.depthBuffer){let BJ=D.depthTexture;if(qJ.__boundDepthTexture!==BJ){if(BJ!==null&&DJ.has(BJ)&&(D.width!==BJ.image.width||D.height!==BJ.image.height))throw new Error("WebGLRenderTarget: Attached DepthTexture is initialized to the incorrect size.");_J.setupDepthRenderbuffer(D)}}let IJ=D.texture;if(IJ.isData3DTexture||IJ.isDataArrayTexture||IJ.isCompressedArrayTexture)YJ=!0;let SJ=DJ.get(D).__webglFramebuffer;if(D.isWebGLCubeRenderTarget){if(Array.isArray(SJ[S]))y=SJ[S][h];else y=SJ[S];t=!0}else if(D.samples>0&&_J.useMultisampledRTT(D)===!1)y=DJ.get(D).__webglMultisampledFramebuffer;else if(Array.isArray(SJ))y=SJ[h];else y=SJ;V.copy(D.viewport),j.copy(D.scissor),m=D.scissorTest}else V.copy(UJ).multiplyScalar(r).floor(),j.copy(TJ).multiplyScalar(r).floor(),m=mJ;if(h!==0)y=NY;if(zJ.bindFramebuffer(I.FRAMEBUFFER,y)&&b)zJ.drawBuffers(D,y);if(zJ.viewport(V),zJ.scissor(j),zJ.setScissorTest(m),t){let qJ=DJ.get(D.texture);I.framebufferTexture2D(I.FRAMEBUFFER,I.COLOR_ATTACHMENT0,I.TEXTURE_CUBE_MAP_POSITIVE_X+S,qJ.__webglTexture,h)}else if(YJ){let qJ=S;for(let IJ=0;IJ<D.textures.length;IJ++){let SJ=DJ.get(D.textures[IJ]);I.framebufferTextureLayer(I.FRAMEBUFFER,I.COLOR_ATTACHMENT0+IJ,SJ.__webglTexture,h,qJ)}}else if(D!==null&&h!==0){let qJ=DJ.get(D.texture);I.framebufferTexture2D(I.FRAMEBUFFER,I.COLOR_ATTACHMENT0,I.TEXTURE_2D,qJ.__webglTexture,h)}x=-1},this.readRenderTargetPixels=function(D,S,h,b,y,t,YJ,OJ=0){if(!(D&&D.isWebGLRenderTarget)){console.error("THREE.WebGLRenderer.readRenderTargetPixels: renderTarget is not THREE.WebGLRenderTarget.");return}let qJ=DJ.get(D).__webglFramebuffer;if(D.isWebGLCubeRenderTarget&&YJ!==void 0)qJ=qJ[YJ];if(qJ){zJ.bindFramebuffer(I.FRAMEBUFFER,qJ);try{let IJ=D.textures[OJ],SJ=IJ.format,BJ=IJ.type;if(!iJ.textureFormatReadable(SJ)){console.error("THREE.WebGLRenderer.readRenderTargetPixels: renderTarget is not in RGBA or implementation defined format.");return}if(!iJ.textureTypeReadable(BJ)){console.error("THREE.WebGLRenderer.readRenderTargetPixels: renderTarget is not in UnsignedByteType or implementation defined type.");return}if(S>=0&&S<=D.width-b&&(h>=0&&h<=D.height-y)){if(D.textures.length>1)I.readBuffer(I.COLOR_ATTACHMENT0+OJ);I.readPixels(S,h,b,y,LJ.convert(SJ),LJ.convert(BJ),t)}}finally{let IJ=T!==null?DJ.get(T).__webglFramebuffer:null;zJ.bindFramebuffer(I.FRAMEBUFFER,IJ)}}},this.readRenderTargetPixelsAsync=async function(D,S,h,b,y,t,YJ,OJ=0){if(!(D&&D.isWebGLRenderTarget))throw new Error("THREE.WebGLRenderer.readRenderTargetPixels: renderTarget is not THREE.WebGLRenderTarget.");let qJ=DJ.get(D).__webglFramebuffer;if(D.isWebGLCubeRenderTarget&&YJ!==void 0)qJ=qJ[YJ];if(qJ)if(S>=0&&S<=D.width-b&&(h>=0&&h<=D.height-y)){zJ.bindFramebuffer(I.FRAMEBUFFER,qJ);let IJ=D.textures[OJ],SJ=IJ.format,BJ=IJ.type;if(!iJ.textureFormatReadable(SJ))throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: renderTarget is not in RGBA or implementation defined format.");if(!iJ.textureTypeReadable(BJ))throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: renderTarget is not in UnsignedByteType or implementation defined type.");let pJ=I.createBuffer();if(I.bindBuffer(I.PIXEL_PACK_BUFFER,pJ),I.bufferData(I.PIXEL_PACK_BUFFER,t.byteLength,I.STREAM_READ),D.textures.length>1)I.readBuffer(I.COLOR_ATTACHMENT0+OJ);I.readPixels(S,h,b,y,LJ.convert(SJ),LJ.convert(BJ),0);let tJ=T!==null?DJ.get(T).__webglFramebuffer:null;zJ.bindFramebuffer(I.FRAMEBUFFER,tJ);let G0=I.fenceSync(I.SYNC_GPU_COMMANDS_COMPLETE,0);return I.flush(),await lW(I,G0,4),I.bindBuffer(I.PIXEL_PACK_BUFFER,pJ),I.getBufferSubData(I.PIXEL_PACK_BUFFER,0,t),I.deleteBuffer(pJ),I.deleteSync(G0),t}else throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: requested read bounds are out of range.")},this.copyFramebufferToTexture=function(D,S=null,h=0){let b=Math.pow(2,-h),y=Math.floor(D.image.width*b),t=Math.floor(D.image.height*b),YJ=S!==null?S.x:0,OJ=S!==null?S.y:0;_J.setTexture2D(D,0),I.copyTexSubImage2D(I.TEXTURE_2D,h,0,0,YJ,OJ,y,t),zJ.unbindTexture()};let OY=I.createFramebuffer(),FY=I.createFramebuffer();if(this.copyTextureToTexture=function(D,S,h=null,b=null,y=0,t=null){if(t===null)if(y!==0)$9("WebGLRenderer: copyTextureToTexture function signature has changed to support src and dst mipmap levels."),t=y,y=0;else t=0;let YJ,OJ,qJ,IJ,SJ,BJ,pJ,tJ,G0,H0=D.isCompressedTexture?D.mipmaps[t]:D.image;if(h!==null)YJ=h.max.x-h.min.x,OJ=h.max.y-h.min.y,qJ=h.isBox3?h.max.z-h.min.z:1,IJ=h.min.x,SJ=h.min.y,BJ=h.isBox3?h.min.z:0;else{let u0=Math.pow(2,-y);if(YJ=Math.floor(H0.width*u0),OJ=Math.floor(H0.height*u0),D.isDataArrayTexture)qJ=H0.depth;else if(D.isData3DTexture)qJ=Math.floor(H0.depth*u0);else qJ=1;IJ=0,SJ=0,BJ=0}if(b!==null)pJ=b.x,tJ=b.y,G0=b.z;else pJ=0,tJ=0,G0=0;let Q0=LJ.convert(S.format),wJ=LJ.convert(S.type),K0;if(S.isData3DTexture)_J.setTexture3D(S,0),K0=I.TEXTURE_3D;else if(S.isDataArrayTexture||S.isCompressedArrayTexture)_J.setTexture2DArray(S,0),K0=I.TEXTURE_2D_ARRAY;else _J.setTexture2D(S,0),K0=I.TEXTURE_2D;I.pixelStorei(I.UNPACK_FLIP_Y_WEBGL,S.flipY),I.pixelStorei(I.UNPACK_PREMULTIPLY_ALPHA_WEBGL,S.premultiplyAlpha),I.pixelStorei(I.UNPACK_ALIGNMENT,S.unpackAlignment);let nJ=I.getParameter(I.UNPACK_ROW_LENGTH),y0=I.getParameter(I.UNPACK_IMAGE_HEIGHT),O9=I.getParameter(I.UNPACK_SKIP_PIXELS),v0=I.getParameter(I.UNPACK_SKIP_ROWS),i9=I.getParameter(I.UNPACK_SKIP_IMAGES);I.pixelStorei(I.UNPACK_ROW_LENGTH,H0.width),I.pixelStorei(I.UNPACK_IMAGE_HEIGHT,H0.height),I.pixelStorei(I.UNPACK_SKIP_PIXELS,IJ),I.pixelStorei(I.UNPACK_SKIP_ROWS,SJ),I.pixelStorei(I.UNPACK_SKIP_IMAGES,BJ);let U0=D.isDataArrayTexture||D.isData3DTexture,m0=S.isDataArrayTexture||S.isData3DTexture;if(D.isDepthTexture){let u0=DJ.get(D),_0=DJ.get(S),T0=DJ.get(u0.__renderTarget),i7=DJ.get(_0.__renderTarget);zJ.bindFramebuffer(I.READ_FRAMEBUFFER,T0.__webglFramebuffer),zJ.bindFramebuffer(I.DRAW_FRAMEBUFFER,i7.__webglFramebuffer);for(let a8=0;a8<qJ;a8++){if(U0)I.framebufferTextureLayer(I.READ_FRAMEBUFFER,I.COLOR_ATTACHMENT0,DJ.get(D).__webglTexture,y,BJ+a8),I.framebufferTextureLayer(I.DRAW_FRAMEBUFFER,I.COLOR_ATTACHMENT0,DJ.get(S).__webglTexture,t,G0+a8);I.blitFramebuffer(IJ,SJ,YJ,OJ,pJ,tJ,YJ,OJ,I.DEPTH_BUFFER_BIT,I.NEAREST)}zJ.bindFramebuffer(I.READ_FRAMEBUFFER,null),zJ.bindFramebuffer(I.DRAW_FRAMEBUFFER,null)}else if(y!==0||D.isRenderTargetTexture||DJ.has(D)){let u0=DJ.get(D),_0=DJ.get(S);zJ.bindFramebuffer(I.READ_FRAMEBUFFER,OY),zJ.bindFramebuffer(I.DRAW_FRAMEBUFFER,FY);for(let T0=0;T0<qJ;T0++){if(U0)I.framebufferTextureLayer(I.READ_FRAMEBUFFER,I.COLOR_ATTACHMENT0,u0.__webglTexture,y,BJ+T0);else I.framebufferTexture2D(I.READ_FRAMEBUFFER,I.COLOR_ATTACHMENT0,I.TEXTURE_2D,u0.__webglTexture,y);if(m0)I.framebufferTextureLayer(I.DRAW_FRAMEBUFFER,I.COLOR_ATTACHMENT0,_0.__webglTexture,t,G0+T0);else I.framebufferTexture2D(I.DRAW_FRAMEBUFFER,I.COLOR_ATTACHMENT0,I.TEXTURE_2D,_0.__webglTexture,t);if(y!==0)I.blitFramebuffer(IJ,SJ,YJ,OJ,pJ,tJ,YJ,OJ,I.COLOR_BUFFER_BIT,I.NEAREST);else if(m0)I.copyTexSubImage3D(K0,t,pJ,tJ,G0+T0,IJ,SJ,YJ,OJ);else I.copyTexSubImage2D(K0,t,pJ,tJ,IJ,SJ,YJ,OJ)}zJ.bindFramebuffer(I.READ_FRAMEBUFFER,null),zJ.bindFramebuffer(I.DRAW_FRAMEBUFFER,null)}else if(m0)if(D.isDataTexture||D.isData3DTexture)I.texSubImage3D(K0,t,pJ,tJ,G0,YJ,OJ,qJ,Q0,wJ,H0.data);else if(S.isCompressedArrayTexture)I.compressedTexSubImage3D(K0,t,pJ,tJ,G0,YJ,OJ,qJ,Q0,H0.data);else I.texSubImage3D(K0,t,pJ,tJ,G0,YJ,OJ,qJ,Q0,wJ,H0);else if(D.isDataTexture)I.texSubImage2D(I.TEXTURE_2D,t,pJ,tJ,YJ,OJ,Q0,wJ,H0.data);else if(D.isCompressedTexture)I.compressedTexSubImage2D(I.TEXTURE_2D,t,pJ,tJ,H0.width,H0.height,Q0,H0.data);else I.texSubImage2D(I.TEXTURE_2D,t,pJ,tJ,YJ,OJ,Q0,wJ,H0);if(I.pixelStorei(I.UNPACK_ROW_LENGTH,nJ),I.pixelStorei(I.UNPACK_IMAGE_HEIGHT,y0),I.pixelStorei(I.UNPACK_SKIP_PIXELS,O9),I.pixelStorei(I.UNPACK_SKIP_ROWS,v0),I.pixelStorei(I.UNPACK_SKIP_IMAGES,i9),t===0&&S.generateMipmaps)I.generateMipmap(K0);zJ.unbindTexture()},this.copyTextureToTexture3D=function(D,S,h=null,b=null,y=0){return $9('WebGLRenderer: copyTextureToTexture3D function has been deprecated. Use "copyTextureToTexture" instead.'),this.copyTextureToTexture(D,S,h,b,y)},this.initRenderTarget=function(D){if(DJ.get(D).__webglFramebuffer===void 0)_J.setupRenderTarget(D)},this.initTexture=function(D){if(D.isCubeTexture)_J.setTextureCube(D,0);else if(D.isData3DTexture)_J.setTexture3D(D,0);else if(D.isDataArrayTexture||D.isCompressedArrayTexture)_J.setTexture2DArray(D,0);else _J.setTexture2D(D,0);zJ.unbindTexture()},this.resetState=function(){v=0,_=0,T=null,zJ.reset(),VJ.reset()},typeof __THREE_DEVTOOLS__!=="undefined")__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}get coordinateSystem(){return E$}get outputColorSpace(){return this._outputColorSpace}set outputColorSpace(J){this._outputColorSpace=J;let Q=this.getContext();Q.drawingBufferColorSpace=lJ._getDrawingBufferColorSpace(J),Q.unpackColorSpace=lJ._getUnpackColorSpace()}}var jH={type:"change"},c$={type:"start"},vH={type:"end"},s7=new m8,yH=new e0,u1=Math.cos(70*X9.DEG2RAD),M0=new A,j0=2*Math.PI,eJ={NONE:-1,ROTATE:0,DOLLY:1,PAN:2,TOUCH_ROTATE:3,TOUCH_PAN:4,TOUCH_DOLLY_PAN:5,TOUCH_DOLLY_ROTATE:6},u$=0.000001;class n$ extends d7{constructor(J,Q=null){super(J,Q);if(this.state=eJ.NONE,this.target=new A,this.cursor=new A,this.minDistance=0,this.maxDistance=1/0,this.minZoom=0,this.maxZoom=1/0,this.minTargetRadius=0,this.maxTargetRadius=1/0,this.minPolarAngle=0,this.maxPolarAngle=Math.PI,this.minAzimuthAngle=-1/0,this.maxAzimuthAngle=1/0,this.enableDamping=!1,this.dampingFactor=0.05,this.enableZoom=!0,this.zoomSpeed=1,this.enableRotate=!0,this.rotateSpeed=1,this.keyRotateSpeed=1,this.enablePan=!0,this.panSpeed=1,this.screenSpacePanning=!0,this.keyPanSpeed=7,this.zoomToCursor=!1,this.autoRotate=!1,this.autoRotateSpeed=2,this.keys={LEFT:"ArrowLeft",UP:"ArrowUp",RIGHT:"ArrowRight",BOTTOM:"ArrowDown"},this.mouseButtons={LEFT:h8.ROTATE,MIDDLE:h8.DOLLY,RIGHT:h8.PAN},this.touches={ONE:b8.ROTATE,TWO:b8.DOLLY_PAN},this.target0=this.target.clone(),this.position0=this.object.position.clone(),this.zoom0=this.object.zoom,this._domElementKeyEvents=null,this._lastPosition=new A,this._lastQuaternion=new A0,this._lastTargetPosition=new A,this._quat=new A0().setFromUnitVectors(J.up,new A(0,1,0)),this._quatInverse=this._quat.clone().invert(),this._spherical=new B6,this._sphericalDelta=new B6,this._scale=1,this._panOffset=new A,this._rotateStart=new PJ,this._rotateEnd=new PJ,this._rotateDelta=new PJ,this._panStart=new PJ,this._panEnd=new PJ,this._panDelta=new PJ,this._dollyStart=new PJ,this._dollyEnd=new PJ,this._dollyDelta=new PJ,this._dollyDirection=new A,this._mouse=new PJ,this._performCursorZoom=!1,this._pointers=[],this._pointerPositions={},this._controlActive=!1,this._onPointerMove=n1.bind(this),this._onPointerDown=c1.bind(this),this._onPointerUp=s1.bind(this),this._onContextMenu=Jq.bind(this),this._onMouseWheel=a1.bind(this),this._onKeyDown=r1.bind(this),this._onTouchStart=t1.bind(this),this._onTouchMove=e1.bind(this),this._onMouseDown=o1.bind(this),this._onMouseMove=i1.bind(this),this._interceptControlDown=Qq.bind(this),this._interceptControlUp=$q.bind(this),this.domElement!==null)this.connect(this.domElement);this.update()}connect(J){super.connect(J),this.domElement.addEventListener("pointerdown",this._onPointerDown),this.domElement.addEventListener("pointercancel",this._onPointerUp),this.domElement.addEventListener("contextmenu",this._onContextMenu),this.domElement.addEventListener("wheel",this._onMouseWheel,{passive:!1}),this.domElement.getRootNode().addEventListener("keydown",this._interceptControlDown,{passive:!0,capture:!0}),this.domElement.style.touchAction="none"}disconnect(){this.domElement.removeEventListener("pointerdown",this._onPointerDown),this.domElement.removeEventListener("pointermove",this._onPointerMove),this.domElement.removeEventListener("pointerup",this._onPointerUp),this.domElement.removeEventListener("pointercancel",this._onPointerUp),this.domElement.removeEventListener("wheel",this._onMouseWheel),this.domElement.removeEventListener("contextmenu",this._onContextMenu),this.stopListenToKeyEvents(),this.domElement.getRootNode().removeEventListener("keydown",this._interceptControlDown,{capture:!0}),this.domElement.style.touchAction="auto"}dispose(){this.disconnect()}getPolarAngle(){return this._spherical.phi}getAzimuthalAngle(){return this._spherical.theta}getDistance(){return this.object.position.distanceTo(this.target)}listenToKeyEvents(J){J.addEventListener("keydown",this._onKeyDown),this._domElementKeyEvents=J}stopListenToKeyEvents(){if(this._domElementKeyEvents!==null)this._domElementKeyEvents.removeEventListener("keydown",this._onKeyDown),this._domElementKeyEvents=null}saveState(){this.target0.copy(this.target),this.position0.copy(this.object.position),this.zoom0=this.object.zoom}reset(){this.target.copy(this.target0),this.object.position.copy(this.position0),this.object.zoom=this.zoom0,this.object.updateProjectionMatrix(),this.dispatchEvent(jH),this.update(),this.state=eJ.NONE}update(J=null){let Q=this.object.position;if(M0.copy(Q).sub(this.target),M0.applyQuaternion(this._quat),this._spherical.setFromVector3(M0),this.autoRotate&&this.state===eJ.NONE)this._rotateLeft(this._getAutoRotationAngle(J));if(this.enableDamping)this._spherical.theta+=this._sphericalDelta.theta*this.dampingFactor,this._spherical.phi+=this._sphericalDelta.phi*this.dampingFactor;else this._spherical.theta+=this._sphericalDelta.theta,this._spherical.phi+=this._sphericalDelta.phi;let $=this.minAzimuthAngle,Z=this.maxAzimuthAngle;if(isFinite($)&&isFinite(Z)){if($<-Math.PI)$+=j0;else if($>Math.PI)$-=j0;if(Z<-Math.PI)Z+=j0;else if(Z>Math.PI)Z-=j0;if($<=Z)this._spherical.theta=Math.max($,Math.min(Z,this._spherical.theta));else this._spherical.theta=this._spherical.theta>($+Z)/2?Math.max($,this._spherical.theta):Math.min(Z,this._spherical.theta)}if(this._spherical.phi=Math.max(this.minPolarAngle,Math.min(this.maxPolarAngle,this._spherical.phi)),this._spherical.makeSafe(),this.enableDamping===!0)this.target.addScaledVector(this._panOffset,this.dampingFactor);else this.target.add(this._panOffset);this.target.sub(this.cursor),this.target.clampLength(this.minTargetRadius,this.maxTargetRadius),this.target.add(this.cursor);let W=!1;if(this.zoomToCursor&&this._performCursorZoom||this.object.isOrthographicCamera)this._spherical.radius=this._clampDistance(this._spherical.radius);else{let H=this._spherical.radius;this._spherical.radius=this._clampDistance(this._spherical.radius*this._scale),W=H!=this._spherical.radius}if(M0.setFromSpherical(this._spherical),M0.applyQuaternion(this._quatInverse),Q.copy(this.target).add(M0),this.object.lookAt(this.target),this.enableDamping===!0)this._sphericalDelta.theta*=1-this.dampingFactor,this._sphericalDelta.phi*=1-this.dampingFactor,this._panOffset.multiplyScalar(1-this.dampingFactor);else this._sphericalDelta.set(0,0,0),this._panOffset.set(0,0,0);if(this.zoomToCursor&&this._performCursorZoom){let H=null;if(this.object.isPerspectiveCamera){let Y=M0.length();H=this._clampDistance(Y*this._scale);let X=Y-H;this.object.position.addScaledVector(this._dollyDirection,X),this.object.updateMatrixWorld(),W=!!X}else if(this.object.isOrthographicCamera){let Y=new A(this._mouse.x,this._mouse.y,0);Y.unproject(this.object);let X=this.object.zoom;this.object.zoom=Math.max(this.minZoom,Math.min(this.maxZoom,this.object.zoom/this._scale)),this.object.updateProjectionMatrix(),W=X!==this.object.zoom;let K=new A(this._mouse.x,this._mouse.y,0);K.unproject(this.object),this.object.position.sub(K).add(Y),this.object.updateMatrixWorld(),H=M0.length()}else console.warn("WARNING: OrbitControls.js encountered an unknown camera type - zoom to cursor disabled."),this.zoomToCursor=!1;if(H!==null)if(this.screenSpacePanning)this.target.set(0,0,-1).transformDirection(this.object.matrix).multiplyScalar(H).add(this.object.position);else if(s7.origin.copy(this.object.position),s7.direction.set(0,0,-1).transformDirection(this.object.matrix),Math.abs(this.object.up.dot(s7.direction))<u1)this.object.lookAt(this.target);else yH.setFromNormalAndCoplanarPoint(this.object.up,this.target),s7.intersectPlane(yH,this.target)}else if(this.object.isOrthographicCamera){let H=this.object.zoom;if(this.object.zoom=Math.max(this.minZoom,Math.min(this.maxZoom,this.object.zoom/this._scale)),H!==this.object.zoom)this.object.updateProjectionMatrix(),W=!0}if(this._scale=1,this._performCursorZoom=!1,W||this._lastPosition.distanceToSquared(this.object.position)>u$||8*(1-this._lastQuaternion.dot(this.object.quaternion))>u$||this._lastTargetPosition.distanceToSquared(this.target)>u$)return this.dispatchEvent(jH),this._lastPosition.copy(this.object.position),this._lastQuaternion.copy(this.object.quaternion),this._lastTargetPosition.copy(this.target),!0;return!1}_getAutoRotationAngle(J){if(J!==null)return j0/60*this.autoRotateSpeed*J;else return j0/60/60*this.autoRotateSpeed}_getZoomScale(J){let Q=Math.abs(J*0.01);return Math.pow(0.95,this.zoomSpeed*Q)}_rotateLeft(J){this._sphericalDelta.theta-=J}_rotateUp(J){this._sphericalDelta.phi-=J}_panLeft(J,Q){M0.setFromMatrixColumn(Q,0),M0.multiplyScalar(-J),this._panOffset.add(M0)}_panUp(J,Q){if(this.screenSpacePanning===!0)M0.setFromMatrixColumn(Q,1);else M0.setFromMatrixColumn(Q,0),M0.crossVectors(this.object.up,M0);M0.multiplyScalar(J),this._panOffset.add(M0)}_pan(J,Q){let $=this.domElement;if(this.object.isPerspectiveCamera){let Z=this.object.position;M0.copy(Z).sub(this.target);let W=M0.length();W*=Math.tan(this.object.fov/2*Math.PI/180),this._panLeft(2*J*W/$.clientHeight,this.object.matrix),this._panUp(2*Q*W/$.clientHeight,this.object.matrix)}else if(this.object.isOrthographicCamera)this._panLeft(J*(this.object.right-this.object.left)/this.object.zoom/$.clientWidth,this.object.matrix),this._panUp(Q*(this.object.top-this.object.bottom)/this.object.zoom/$.clientHeight,this.object.matrix);else console.warn("WARNING: OrbitControls.js encountered an unknown camera type - pan disabled."),this.enablePan=!1}_dollyOut(J){if(this.object.isPerspectiveCamera||this.object.isOrthographicCamera)this._scale/=J;else console.warn("WARNING: OrbitControls.js encountered an unknown camera type - dolly/zoom disabled."),this.enableZoom=!1}_dollyIn(J){if(this.object.isPerspectiveCamera||this.object.isOrthographicCamera)this._scale*=J;else console.warn("WARNING: OrbitControls.js encountered an unknown camera type - dolly/zoom disabled."),this.enableZoom=!1}_updateZoomParameters(J,Q){if(!this.zoomToCursor)return;this._performCursorZoom=!0;let $=this.domElement.getBoundingClientRect(),Z=J-$.left,W=Q-$.top,H=$.width,Y=$.height;this._mouse.x=Z/H*2-1,this._mouse.y=-(W/Y)*2+1,this._dollyDirection.set(this._mouse.x,this._mouse.y,1).unproject(this.object).sub(this.object.position).normalize()}_clampDistance(J){return Math.max(this.minDistance,Math.min(this.maxDistance,J))}_handleMouseDownRotate(J){this._rotateStart.set(J.clientX,J.clientY)}_handleMouseDownDolly(J){this._updateZoomParameters(J.clientX,J.clientX),this._dollyStart.set(J.clientX,J.clientY)}_handleMouseDownPan(J){this._panStart.set(J.clientX,J.clientY)}_handleMouseMoveRotate(J){this._rotateEnd.set(J.clientX,J.clientY),this._rotateDelta.subVectors(this._rotateEnd,this._rotateStart).multiplyScalar(this.rotateSpeed);let Q=this.domElement;this._rotateLeft(j0*this._rotateDelta.x/Q.clientHeight),this._rotateUp(j0*this._rotateDelta.y/Q.clientHeight),this._rotateStart.copy(this._rotateEnd),this.update()}_handleMouseMoveDolly(J){if(this._dollyEnd.set(J.clientX,J.clientY),this._dollyDelta.subVectors(this._dollyEnd,this._dollyStart),this._dollyDelta.y>0)this._dollyOut(this._getZoomScale(this._dollyDelta.y));else if(this._dollyDelta.y<0)this._dollyIn(this._getZoomScale(this._dollyDelta.y));this._dollyStart.copy(this._dollyEnd),this.update()}_handleMouseMovePan(J){this._panEnd.set(J.clientX,J.clientY),this._panDelta.subVectors(this._panEnd,this._panStart).multiplyScalar(this.panSpeed),this._pan(this._panDelta.x,this._panDelta.y),this._panStart.copy(this._panEnd),this.update()}_handleMouseWheel(J){if(this._updateZoomParameters(J.clientX,J.clientY),J.deltaY<0)this._dollyIn(this._getZoomScale(J.deltaY));else if(J.deltaY>0)this._dollyOut(this._getZoomScale(J.deltaY));this.update()}_handleKeyDown(J){let Q=!1;switch(J.code){case this.keys.UP:if(J.ctrlKey||J.metaKey||J.shiftKey){if(this.enableRotate)this._rotateUp(j0*this.keyRotateSpeed/this.domElement.clientHeight)}else if(this.enablePan)this._pan(0,this.keyPanSpeed);Q=!0;break;case this.keys.BOTTOM:if(J.ctrlKey||J.metaKey||J.shiftKey){if(this.enableRotate)this._rotateUp(-j0*this.keyRotateSpeed/this.domElement.clientHeight)}else if(this.enablePan)this._pan(0,-this.keyPanSpeed);Q=!0;break;case this.keys.LEFT:if(J.ctrlKey||J.metaKey||J.shiftKey){if(this.enableRotate)this._rotateLeft(j0*this.keyRotateSpeed/this.domElement.clientHeight)}else if(this.enablePan)this._pan(this.keyPanSpeed,0);Q=!0;break;case this.keys.RIGHT:if(J.ctrlKey||J.metaKey||J.shiftKey){if(this.enableRotate)this._rotateLeft(-j0*this.keyRotateSpeed/this.domElement.clientHeight)}else if(this.enablePan)this._pan(-this.keyPanSpeed,0);Q=!0;break}if(Q)J.preventDefault(),this.update()}_handleTouchStartRotate(J){if(this._pointers.length===1)this._rotateStart.set(J.pageX,J.pageY);else{let Q=this._getSecondPointerPosition(J),$=0.5*(J.pageX+Q.x),Z=0.5*(J.pageY+Q.y);this._rotateStart.set($,Z)}}_handleTouchStartPan(J){if(this._pointers.length===1)this._panStart.set(J.pageX,J.pageY);else{let Q=this._getSecondPointerPosition(J),$=0.5*(J.pageX+Q.x),Z=0.5*(J.pageY+Q.y);this._panStart.set($,Z)}}_handleTouchStartDolly(J){let Q=this._getSecondPointerPosition(J),$=J.pageX-Q.x,Z=J.pageY-Q.y,W=Math.sqrt($*$+Z*Z);this._dollyStart.set(0,W)}_handleTouchStartDollyPan(J){if(this.enableZoom)this._handleTouchStartDolly(J);if(this.enablePan)this._handleTouchStartPan(J)}_handleTouchStartDollyRotate(J){if(this.enableZoom)this._handleTouchStartDolly(J);if(this.enableRotate)this._handleTouchStartRotate(J)}_handleTouchMoveRotate(J){if(this._pointers.length==1)this._rotateEnd.set(J.pageX,J.pageY);else{let $=this._getSecondPointerPosition(J),Z=0.5*(J.pageX+$.x),W=0.5*(J.pageY+$.y);this._rotateEnd.set(Z,W)}this._rotateDelta.subVectors(this._rotateEnd,this._rotateStart).multiplyScalar(this.rotateSpeed);let Q=this.domElement;this._rotateLeft(j0*this._rotateDelta.x/Q.clientHeight),this._rotateUp(j0*this._rotateDelta.y/Q.clientHeight),this._rotateStart.copy(this._rotateEnd)}_handleTouchMovePan(J){if(this._pointers.length===1)this._panEnd.set(J.pageX,J.pageY);else{let Q=this._getSecondPointerPosition(J),$=0.5*(J.pageX+Q.x),Z=0.5*(J.pageY+Q.y);this._panEnd.set($,Z)}this._panDelta.subVectors(this._panEnd,this._panStart).multiplyScalar(this.panSpeed),this._pan(this._panDelta.x,this._panDelta.y),this._panStart.copy(this._panEnd)}_handleTouchMoveDolly(J){let Q=this._getSecondPointerPosition(J),$=J.pageX-Q.x,Z=J.pageY-Q.y,W=Math.sqrt($*$+Z*Z);this._dollyEnd.set(0,W),this._dollyDelta.set(0,Math.pow(this._dollyEnd.y/this._dollyStart.y,this.zoomSpeed)),this._dollyOut(this._dollyDelta.y),this._dollyStart.copy(this._dollyEnd);let H=(J.pageX+Q.x)*0.5,Y=(J.pageY+Q.y)*0.5;this._updateZoomParameters(H,Y)}_handleTouchMoveDollyPan(J){if(this.enableZoom)this._handleTouchMoveDolly(J);if(this.enablePan)this._handleTouchMovePan(J)}_handleTouchMoveDollyRotate(J){if(this.enableZoom)this._handleTouchMoveDolly(J);if(this.enableRotate)this._handleTouchMoveRotate(J)}_addPointer(J){this._pointers.push(J.pointerId)}_removePointer(J){delete this._pointerPositions[J.pointerId];for(let Q=0;Q<this._pointers.length;Q++)if(this._pointers[Q]==J.pointerId){this._pointers.splice(Q,1);return}}_isTrackingPointer(J){for(let Q=0;Q<this._pointers.length;Q++)if(this._pointers[Q]==J.pointerId)return!0;return!1}_trackPointer(J){let Q=this._pointerPositions[J.pointerId];if(Q===void 0)Q=new PJ,this._pointerPositions[J.pointerId]=Q;Q.set(J.pageX,J.pageY)}_getSecondPointerPosition(J){let Q=J.pointerId===this._pointers[0]?this._pointers[1]:this._pointers[0];return this._pointerPositions[Q]}_customWheelEvent(J){let Q=J.deltaMode,$={clientX:J.clientX,clientY:J.clientY,deltaY:J.deltaY};switch(Q){case 1:$.deltaY*=16;break;case 2:$.deltaY*=100;break}if(J.ctrlKey&&!this._controlActive)$.deltaY*=10;return $}}function c1(J){if(this.enabled===!1)return;if(this._pointers.length===0)this.domElement.setPointerCapture(J.pointerId),this.domElement.addEventListener("pointermove",this._onPointerMove),this.domElement.addEventListener("pointerup",this._onPointerUp);if(this._isTrackingPointer(J))return;if(this._addPointer(J),J.pointerType==="touch")this._onTouchStart(J);else this._onMouseDown(J)}function n1(J){if(this.enabled===!1)return;if(J.pointerType==="touch")this._onTouchMove(J);else this._onMouseMove(J)}function s1(J){switch(this._removePointer(J),this._pointers.length){case 0:this.domElement.releasePointerCapture(J.pointerId),this.domElement.removeEventListener("pointermove",this._onPointerMove),this.domElement.removeEventListener("pointerup",this._onPointerUp),this.dispatchEvent(vH),this.state=eJ.NONE;break;case 1:let Q=this._pointers[0],$=this._pointerPositions[Q];this._onTouchStart({pointerId:Q,pageX:$.x,pageY:$.y});break}}function o1(J){let Q;switch(J.button){case 0:Q=this.mouseButtons.LEFT;break;case 1:Q=this.mouseButtons.MIDDLE;break;case 2:Q=this.mouseButtons.RIGHT;break;default:Q=-1}switch(Q){case h8.DOLLY:if(this.enableZoom===!1)return;this._handleMouseDownDolly(J),this.state=eJ.DOLLY;break;case h8.ROTATE:if(J.ctrlKey||J.metaKey||J.shiftKey){if(this.enablePan===!1)return;this._handleMouseDownPan(J),this.state=eJ.PAN}else{if(this.enableRotate===!1)return;this._handleMouseDownRotate(J),this.state=eJ.ROTATE}break;case h8.PAN:if(J.ctrlKey||J.metaKey||J.shiftKey){if(this.enableRotate===!1)return;this._handleMouseDownRotate(J),this.state=eJ.ROTATE}else{if(this.enablePan===!1)return;this._handleMouseDownPan(J),this.state=eJ.PAN}break;default:this.state=eJ.NONE}if(this.state!==eJ.NONE)this.dispatchEvent(c$)}function i1(J){switch(this.state){case eJ.ROTATE:if(this.enableRotate===!1)return;this._handleMouseMoveRotate(J);break;case eJ.DOLLY:if(this.enableZoom===!1)return;this._handleMouseMoveDolly(J);break;case eJ.PAN:if(this.enablePan===!1)return;this._handleMouseMovePan(J);break}}function a1(J){if(this.enabled===!1||this.enableZoom===!1||this.state!==eJ.NONE)return;J.preventDefault(),this.dispatchEvent(c$),this._handleMouseWheel(this._customWheelEvent(J)),this.dispatchEvent(vH)}function r1(J){if(this.enabled===!1)return;this._handleKeyDown(J)}function t1(J){switch(this._trackPointer(J),this._pointers.length){case 1:switch(this.touches.ONE){case b8.ROTATE:if(this.enableRotate===!1)return;this._handleTouchStartRotate(J),this.state=eJ.TOUCH_ROTATE;break;case b8.PAN:if(this.enablePan===!1)return;this._handleTouchStartPan(J),this.state=eJ.TOUCH_PAN;break;default:this.state=eJ.NONE}break;case 2:switch(this.touches.TWO){case b8.DOLLY_PAN:if(this.enableZoom===!1&&this.enablePan===!1)return;this._handleTouchStartDollyPan(J),this.state=eJ.TOUCH_DOLLY_PAN;break;case b8.DOLLY_ROTATE:if(this.enableZoom===!1&&this.enableRotate===!1)return;this._handleTouchStartDollyRotate(J),this.state=eJ.TOUCH_DOLLY_ROTATE;break;default:this.state=eJ.NONE}break;default:this.state=eJ.NONE}if(this.state!==eJ.NONE)this.dispatchEvent(c$)}function e1(J){switch(this._trackPointer(J),this.state){case eJ.TOUCH_ROTATE:if(this.enableRotate===!1)return;this._handleTouchMoveRotate(J),this.update();break;case eJ.TOUCH_PAN:if(this.enablePan===!1)return;this._handleTouchMovePan(J),this.update();break;case eJ.TOUCH_DOLLY_PAN:if(this.enableZoom===!1&&this.enablePan===!1)return;this._handleTouchMoveDollyPan(J),this.update();break;case eJ.TOUCH_DOLLY_ROTATE:if(this.enableZoom===!1&&this.enableRotate===!1)return;this._handleTouchMoveDollyRotate(J),this.update();break;default:this.state=eJ.NONE}}function Jq(J){if(this.enabled===!1)return;J.preventDefault()}function Qq(J){if(J.key==="Control")this._controlActive=!0,this.domElement.getRootNode().addEventListener("keyup",this._interceptControlUp,{passive:!0,capture:!0})}function $q(J){if(J.key==="Control")this._controlActive=!1,this.domElement.getRootNode().removeEventListener("keyup",this._interceptControlUp,{passive:!0,capture:!0})}function s$(J,Q){if(Q===K$)return console.warn("THREE.BufferGeometryUtils.toTrianglesDrawMode(): Geometry already defined as triangles."),J;if(Q===b9||Q===E6){let $=J.getIndex();if($===null){let Y=[],X=J.getAttribute("position");if(X!==void 0){for(let K=0;K<X.count;K++)Y.push(K);J.setIndex(Y),$=J.getIndex()}else return console.error("THREE.BufferGeometryUtils.toTrianglesDrawMode(): Undefined position attribute. Processing not possible."),J}let Z=$.count-2,W=[];if(Q===b9)for(let Y=1;Y<=Z;Y++)W.push($.getX(0)),W.push($.getX(Y)),W.push($.getX(Y+1));else for(let Y=0;Y<Z;Y++)if(Y%2===0)W.push($.getX(Y)),W.push($.getX(Y+1)),W.push($.getX(Y+2));else W.push($.getX(Y+2)),W.push($.getX(Y+1)),W.push($.getX(Y));if(W.length/3!==Z)console.error("THREE.BufferGeometryUtils.toTrianglesDrawMode(): Unable to generate correct amount of triangles.");let H=J.clone();return H.setIndex(W),H.clearGroups(),H}else return console.error("THREE.BufferGeometryUtils.toTrianglesDrawMode(): Unknown draw mode:",Q),J}class e$ extends P8{constructor(J){super(J);this.dracoLoader=null,this.ktx2Loader=null,this.meshoptDecoder=null,this.pluginCallbacks=[],this.register(function(Q){return new dH(Q)}),this.register(function(Q){return new mH(Q)}),this.register(function(Q){return new tH(Q)}),this.register(function(Q){return new eH(Q)}),this.register(function(Q){return new JY(Q)}),this.register(function(Q){return new cH(Q)}),this.register(function(Q){return new nH(Q)}),this.register(function(Q){return new sH(Q)}),this.register(function(Q){return new oH(Q)}),this.register(function(Q){return new lH(Q)}),this.register(function(Q){return new iH(Q)}),this.register(function(Q){return new uH(Q)}),this.register(function(Q){return new rH(Q)}),this.register(function(Q){return new aH(Q)}),this.register(function(Q){return new gH(Q)}),this.register(function(Q){return new QY(Q)}),this.register(function(Q){return new $Y(Q)})}load(J,Q,$,Z){let W=this,H;if(this.resourcePath!=="")H=this.resourcePath;else if(this.path!==""){let K=s8.extractUrlBase(J);H=s8.resolveURL(K,this.path)}else H=s8.extractUrlBase(J);this.manager.itemStart(J);let Y=function(K){if(Z)Z(K);else console.error(K);W.manager.itemError(J),W.manager.itemEnd(J)},X=new z6(this.manager);X.setPath(this.path),X.setResponseType("arraybuffer"),X.setRequestHeader(this.requestHeader),X.setWithCredentials(this.withCredentials),X.load(J,function(K){try{W.parse(K,H,function(U){Q(U),W.manager.itemEnd(J)},Y)}catch(U){Y(U)}},$,Y)}setDRACOLoader(J){return this.dracoLoader=J,this}setKTX2Loader(J){return this.ktx2Loader=J,this}setMeshoptDecoder(J){return this.meshoptDecoder=J,this}register(J){if(this.pluginCallbacks.indexOf(J)===-1)this.pluginCallbacks.push(J);return this}unregister(J){if(this.pluginCallbacks.indexOf(J)!==-1)this.pluginCallbacks.splice(this.pluginCallbacks.indexOf(J),1);return this}parse(J,Q,$,Z){let W,H={},Y={},X=new TextDecoder;if(typeof J==="string")W=JSON.parse(J);else if(J instanceof ArrayBuffer)if(X.decode(new Uint8Array(J,0,4))===ZY){try{H[gJ.KHR_BINARY_GLTF]=new WY(J)}catch(G){if(Z)Z(G);return}W=JSON.parse(H[gJ.KHR_BINARY_GLTF].content)}else W=JSON.parse(X.decode(J));else W=J;if(W.asset===void 0||W.asset.version[0]<2){if(Z)Z(new Error("THREE.GLTFLoader: Unsupported asset. glTF versions >=2.0 are supported."));return}let K=new UY(W,{path:Q||this.resourcePath||"",crossOrigin:this.crossOrigin,requestHeader:this.requestHeader,manager:this.manager,ktx2Loader:this.ktx2Loader,meshoptDecoder:this.meshoptDecoder});K.fileLoader.setRequestHeader(this.requestHeader);for(let U=0;U<this.pluginCallbacks.length;U++){let G=this.pluginCallbacks[U](K);if(!G.name)console.error("THREE.GLTFLoader: Invalid plugin found: missing name");Y[G.name]=G,H[G.name]=!0}if(W.extensionsUsed)for(let U=0;U<W.extensionsUsed.length;++U){let G=W.extensionsUsed[U],q=W.extensionsRequired||[];switch(G){case gJ.KHR_MATERIALS_UNLIT:H[G]=new pH;break;case gJ.KHR_DRACO_MESH_COMPRESSION:H[G]=new HY(W,this.dracoLoader);break;case gJ.KHR_TEXTURE_TRANSFORM:H[G]=new YY;break;case gJ.KHR_MESH_QUANTIZATION:H[G]=new XY;break;default:if(q.indexOf(G)>=0&&Y[G]===void 0)console.warn('THREE.GLTFLoader: Unknown extension "'+G+'".')}}K.setExtensions(H),K.setPlugins(Y),K.parse($,Z)}parseAsync(J,Q){let $=this;return new Promise(function(Z,W){$.parse(J,Q,Z,W)})}}function Zq(){let J={};return{get:function(Q){return J[Q]},add:function(Q,$){J[Q]=$},remove:function(Q){delete J[Q]},removeAll:function(){J={}}}}var gJ={KHR_BINARY_GLTF:"KHR_binary_glTF",KHR_DRACO_MESH_COMPRESSION:"KHR_draco_mesh_compression",KHR_LIGHTS_PUNCTUAL:"KHR_lights_punctual",KHR_MATERIALS_CLEARCOAT:"KHR_materials_clearcoat",KHR_MATERIALS_DISPERSION:"KHR_materials_dispersion",KHR_MATERIALS_IOR:"KHR_materials_ior",KHR_MATERIALS_SHEEN:"KHR_materials_sheen",KHR_MATERIALS_SPECULAR:"KHR_materials_specular",KHR_MATERIALS_TRANSMISSION:"KHR_materials_transmission",KHR_MATERIALS_IRIDESCENCE:"KHR_materials_iridescence",KHR_MATERIALS_ANISOTROPY:"KHR_materials_anisotropy",KHR_MATERIALS_UNLIT:"KHR_materials_unlit",KHR_MATERIALS_VOLUME:"KHR_materials_volume",KHR_TEXTURE_BASISU:"KHR_texture_basisu",KHR_TEXTURE_TRANSFORM:"KHR_texture_transform",KHR_MESH_QUANTIZATION:"KHR_mesh_quantization",KHR_MATERIALS_EMISSIVE_STRENGTH:"KHR_materials_emissive_strength",EXT_MATERIALS_BUMP:"EXT_materials_bump",EXT_TEXTURE_WEBP:"EXT_texture_webp",EXT_TEXTURE_AVIF:"EXT_texture_avif",EXT_MESHOPT_COMPRESSION:"EXT_meshopt_compression",EXT_MESH_GPU_INSTANCING:"EXT_mesh_gpu_instancing"};class gH{constructor(J){this.parser=J,this.name=gJ.KHR_LIGHTS_PUNCTUAL,this.cache={refs:{},uses:{}}}_markDefs(){let J=this.parser,Q=this.parser.json.nodes||[];for(let $=0,Z=Q.length;$<Z;$++){let W=Q[$];if(W.extensions&&W.extensions[this.name]&&W.extensions[this.name].light!==void 0)J._addNodeRef(this.cache,W.extensions[this.name].light)}}_loadLight(J){let Q=this.parser,$="light:"+J,Z=Q.cache.get($);if(Z)return Z;let W=Q.json,X=((W.extensions&&W.extensions[this.name]||{}).lights||[])[J],K,U=new jJ(16777215);if(X.color!==void 0)U.setRGB(X.color[0],X.color[1],X.color[2],P0);let G=X.range!==void 0?X.range:0;switch(X.type){case"directional":K=new u9(U),K.target.position.set(0,0,-1),K.add(K.target);break;case"point":K=new p7(U),K.distance=G;break;case"spot":K=new g7(U),K.distance=G,X.spot=X.spot||{},X.spot.innerConeAngle=X.spot.innerConeAngle!==void 0?X.spot.innerConeAngle:0,X.spot.outerConeAngle=X.spot.outerConeAngle!==void 0?X.spot.outerConeAngle:Math.PI/4,K.angle=X.spot.outerConeAngle,K.penumbra=1-X.spot.innerConeAngle/X.spot.outerConeAngle,K.target.position.set(0,0,-1),K.add(K.target);break;default:throw new Error("THREE.GLTFLoader: Unexpected light type: "+X.type)}if(K.position.set(0,0,0),T8(K,X),X.intensity!==void 0)K.intensity=X.intensity;return K.name=Q.createUniqueName(X.name||"light_"+J),Z=Promise.resolve(K),Q.cache.add($,Z),Z}getDependency(J,Q){if(J!=="light")return;return this._loadLight(Q)}createNodeAttachment(J){let Q=this,$=this.parser,W=$.json.nodes[J],Y=(W.extensions&&W.extensions[this.name]||{}).light;if(Y===void 0)return null;return this._loadLight(Y).then(function(X){return $._getNodeRef(Q.cache,Y,X)})}}class pH{constructor(){this.name=gJ.KHR_MATERIALS_UNLIT}getMaterialType(){return G8}extendParams(J,Q,$){let Z=[];J.color=new jJ(1,1,1),J.opacity=1;let W=Q.pbrMetallicRoughness;if(W){if(Array.isArray(W.baseColorFactor)){let H=W.baseColorFactor;J.color.setRGB(H[0],H[1],H[2],P0),J.opacity=H[3]}if(W.baseColorTexture!==void 0)Z.push($.assignTexture(J,"map",W.baseColorTexture,d8))}return Promise.all(Z)}}class lH{constructor(J){this.parser=J,this.name=gJ.KHR_MATERIALS_EMISSIVE_STRENGTH}extendMaterialParams(J,Q){let Z=this.parser.json.materials[J];if(!Z.extensions||!Z.extensions[this.name])return Promise.resolve();let W=Z.extensions[this.name].emissiveStrength;if(W!==void 0)Q.emissiveIntensity=W;return Promise.resolve()}}class dH{constructor(J){this.parser=J,this.name=gJ.KHR_MATERIALS_CLEARCOAT}getMaterialType(J){let $=this.parser.json.materials[J];if(!$.extensions||!$.extensions[this.name])return null;return l0}extendMaterialParams(J,Q){let $=this.parser,Z=$.json.materials[J];if(!Z.extensions||!Z.extensions[this.name])return Promise.resolve();let W=[],H=Z.extensions[this.name];if(H.clearcoatFactor!==void 0)Q.clearcoat=H.clearcoatFactor;if(H.clearcoatTexture!==void 0)W.push($.assignTexture(Q,"clearcoatMap",H.clearcoatTexture));if(H.clearcoatRoughnessFactor!==void 0)Q.clearcoatRoughness=H.clearcoatRoughnessFactor;if(H.clearcoatRoughnessTexture!==void 0)W.push($.assignTexture(Q,"clearcoatRoughnessMap",H.clearcoatRoughnessTexture));if(H.clearcoatNormalTexture!==void 0){if(W.push($.assignTexture(Q,"clearcoatNormalMap",H.clearcoatNormalTexture)),H.clearcoatNormalTexture.scale!==void 0){let Y=H.clearcoatNormalTexture.scale;Q.clearcoatNormalScale=new PJ(Y,Y)}}return Promise.all(W)}}class mH{constructor(J){this.parser=J,this.name=gJ.KHR_MATERIALS_DISPERSION}getMaterialType(J){let $=this.parser.json.materials[J];if(!$.extensions||!$.extensions[this.name])return null;return l0}extendMaterialParams(J,Q){let Z=this.parser.json.materials[J];if(!Z.extensions||!Z.extensions[this.name])return Promise.resolve();let W=Z.extensions[this.name];return Q.dispersion=W.dispersion!==void 0?W.dispersion:0,Promise.resolve()}}class uH{constructor(J){this.parser=J,this.name=gJ.KHR_MATERIALS_IRIDESCENCE}getMaterialType(J){let $=this.parser.json.materials[J];if(!$.extensions||!$.extensions[this.name])return null;return l0}extendMaterialParams(J,Q){let $=this.parser,Z=$.json.materials[J];if(!Z.extensions||!Z.extensions[this.name])return Promise.resolve();let W=[],H=Z.extensions[this.name];if(H.iridescenceFactor!==void 0)Q.iridescence=H.iridescenceFactor;if(H.iridescenceTexture!==void 0)W.push($.assignTexture(Q,"iridescenceMap",H.iridescenceTexture));if(H.iridescenceIor!==void 0)Q.iridescenceIOR=H.iridescenceIor;if(Q.iridescenceThicknessRange===void 0)Q.iridescenceThicknessRange=[100,400];if(H.iridescenceThicknessMinimum!==void 0)Q.iridescenceThicknessRange[0]=H.iridescenceThicknessMinimum;if(H.iridescenceThicknessMaximum!==void 0)Q.iridescenceThicknessRange[1]=H.iridescenceThicknessMaximum;if(H.iridescenceThicknessTexture!==void 0)W.push($.assignTexture(Q,"iridescenceThicknessMap",H.iridescenceThicknessTexture));return Promise.all(W)}}class cH{constructor(J){this.parser=J,this.name=gJ.KHR_MATERIALS_SHEEN}getMaterialType(J){let $=this.parser.json.materials[J];if(!$.extensions||!$.extensions[this.name])return null;return l0}extendMaterialParams(J,Q){let $=this.parser,Z=$.json.materials[J];if(!Z.extensions||!Z.extensions[this.name])return Promise.resolve();let W=[];Q.sheenColor=new jJ(0,0,0),Q.sheenRoughness=0,Q.sheen=1;let H=Z.extensions[this.name];if(H.sheenColorFactor!==void 0){let Y=H.sheenColorFactor;Q.sheenColor.setRGB(Y[0],Y[1],Y[2],P0)}if(H.sheenRoughnessFactor!==void 0)Q.sheenRoughness=H.sheenRoughnessFactor;if(H.sheenColorTexture!==void 0)W.push($.assignTexture(Q,"sheenColorMap",H.sheenColorTexture,d8));if(H.sheenRoughnessTexture!==void 0)W.push($.assignTexture(Q,"sheenRoughnessMap",H.sheenRoughnessTexture));return Promise.all(W)}}class nH{constructor(J){this.parser=J,this.name=gJ.KHR_MATERIALS_TRANSMISSION}getMaterialType(J){let $=this.parser.json.materials[J];if(!$.extensions||!$.extensions[this.name])return null;return l0}extendMaterialParams(J,Q){let $=this.parser,Z=$.json.materials[J];if(!Z.extensions||!Z.extensions[this.name])return Promise.resolve();let W=[],H=Z.extensions[this.name];if(H.transmissionFactor!==void 0)Q.transmission=H.transmissionFactor;if(H.transmissionTexture!==void 0)W.push($.assignTexture(Q,"transmissionMap",H.transmissionTexture));return Promise.all(W)}}class sH{constructor(J){this.parser=J,this.name=gJ.KHR_MATERIALS_VOLUME}getMaterialType(J){let $=this.parser.json.materials[J];if(!$.extensions||!$.extensions[this.name])return null;return l0}extendMaterialParams(J,Q){let $=this.parser,Z=$.json.materials[J];if(!Z.extensions||!Z.extensions[this.name])return Promise.resolve();let W=[],H=Z.extensions[this.name];if(Q.thickness=H.thicknessFactor!==void 0?H.thicknessFactor:0,H.thicknessTexture!==void 0)W.push($.assignTexture(Q,"thicknessMap",H.thicknessTexture));Q.attenuationDistance=H.attenuationDistance||1/0;let Y=H.attenuationColor||[1,1,1];return Q.attenuationColor=new jJ().setRGB(Y[0],Y[1],Y[2],P0),Promise.all(W)}}class oH{constructor(J){this.parser=J,this.name=gJ.KHR_MATERIALS_IOR}getMaterialType(J){let $=this.parser.json.materials[J];if(!$.extensions||!$.extensions[this.name])return null;return l0}extendMaterialParams(J,Q){let Z=this.parser.json.materials[J];if(!Z.extensions||!Z.extensions[this.name])return Promise.resolve();let W=Z.extensions[this.name];return Q.ior=W.ior!==void 0?W.ior:1.5,Promise.resolve()}}class iH{constructor(J){this.parser=J,this.name=gJ.KHR_MATERIALS_SPECULAR}getMaterialType(J){let $=this.parser.json.materials[J];if(!$.extensions||!$.extensions[this.name])return null;return l0}extendMaterialParams(J,Q){let $=this.parser,Z=$.json.materials[J];if(!Z.extensions||!Z.extensions[this.name])return Promise.resolve();let W=[],H=Z.extensions[this.name];if(Q.specularIntensity=H.specularFactor!==void 0?H.specularFactor:1,H.specularTexture!==void 0)W.push($.assignTexture(Q,"specularIntensityMap",H.specularTexture));let Y=H.specularColorFactor||[1,1,1];if(Q.specularColor=new jJ().setRGB(Y[0],Y[1],Y[2],P0),H.specularColorTexture!==void 0)W.push($.assignTexture(Q,"specularColorMap",H.specularColorTexture,d8));return Promise.all(W)}}class aH{constructor(J){this.parser=J,this.name=gJ.EXT_MATERIALS_BUMP}getMaterialType(J){let $=this.parser.json.materials[J];if(!$.extensions||!$.extensions[this.name])return null;return l0}extendMaterialParams(J,Q){let $=this.parser,Z=$.json.materials[J];if(!Z.extensions||!Z.extensions[this.name])return Promise.resolve();let W=[],H=Z.extensions[this.name];if(Q.bumpScale=H.bumpFactor!==void 0?H.bumpFactor:1,H.bumpTexture!==void 0)W.push($.assignTexture(Q,"bumpMap",H.bumpTexture));return Promise.all(W)}}class rH{constructor(J){this.parser=J,this.name=gJ.KHR_MATERIALS_ANISOTROPY}getMaterialType(J){let $=this.parser.json.materials[J];if(!$.extensions||!$.extensions[this.name])return null;return l0}extendMaterialParams(J,Q){let $=this.parser,Z=$.json.materials[J];if(!Z.extensions||!Z.extensions[this.name])return Promise.resolve();let W=[],H=Z.extensions[this.name];if(H.anisotropyStrength!==void 0)Q.anisotropy=H.anisotropyStrength;if(H.anisotropyRotation!==void 0)Q.anisotropyRotation=H.anisotropyRotation;if(H.anisotropyTexture!==void 0)W.push($.assignTexture(Q,"anisotropyMap",H.anisotropyTexture));return Promise.all(W)}}class tH{constructor(J){this.parser=J,this.name=gJ.KHR_TEXTURE_BASISU}loadTexture(J){let Q=this.parser,$=Q.json,Z=$.textures[J];if(!Z.extensions||!Z.extensions[this.name])return null;let W=Z.extensions[this.name],H=Q.options.ktx2Loader;if(!H)if($.extensionsRequired&&$.extensionsRequired.indexOf(this.name)>=0)throw new Error("THREE.GLTFLoader: setKTX2Loader must be called before loading KTX2 textures");else return null;return Q.loadTextureImage(J,W.source,H)}}class eH{constructor(J){this.parser=J,this.name=gJ.EXT_TEXTURE_WEBP}loadTexture(J){let Q=this.name,$=this.parser,Z=$.json,W=Z.textures[J];if(!W.extensions||!W.extensions[Q])return null;let H=W.extensions[Q],Y=Z.images[H.source],X=$.textureLoader;if(Y.uri){let K=$.options.manager.getHandler(Y.uri);if(K!==null)X=K}return $.loadTextureImage(J,H.source,X)}}class JY{constructor(J){this.parser=J,this.name=gJ.EXT_TEXTURE_AVIF}loadTexture(J){let Q=this.name,$=this.parser,Z=$.json,W=Z.textures[J];if(!W.extensions||!W.extensions[Q])return null;let H=W.extensions[Q],Y=Z.images[H.source],X=$.textureLoader;if(Y.uri){let K=$.options.manager.getHandler(Y.uri);if(K!==null)X=K}return $.loadTextureImage(J,H.source,X)}}class QY{constructor(J){this.name=gJ.EXT_MESHOPT_COMPRESSION,this.parser=J}loadBufferView(J){let Q=this.parser.json,$=Q.bufferViews[J];if($.extensions&&$.extensions[this.name]){let Z=$.extensions[this.name],W=this.parser.getDependency("buffer",Z.buffer),H=this.parser.options.meshoptDecoder;if(!H||!H.supported)if(Q.extensionsRequired&&Q.extensionsRequired.indexOf(this.name)>=0)throw new Error("THREE.GLTFLoader: setMeshoptDecoder must be called before loading compressed files");else return null;return W.then(function(Y){let X=Z.byteOffset||0,K=Z.byteLength||0,U=Z.count,G=Z.byteStride,q=new Uint8Array(Y,X,K);if(H.decodeGltfBufferAsync)return H.decodeGltfBufferAsync(U,G,q,Z.mode,Z.filter).then(function(E){return E.buffer});else return H.ready.then(function(){let E=new ArrayBuffer(U*G);return H.decodeGltfBuffer(new Uint8Array(E),U,G,q,Z.mode,Z.filter),E})})}else return null}}class $Y{constructor(J){this.name=gJ.EXT_MESH_GPU_INSTANCING,this.parser=J}createNodeMesh(J){let Q=this.parser.json,$=Q.nodes[J];if(!$.extensions||!$.extensions[this.name]||$.mesh===void 0)return null;let Z=Q.meshes[$.mesh];for(let K of Z.primitives)if(K.mode!==i0.TRIANGLES&&K.mode!==i0.TRIANGLE_STRIP&&K.mode!==i0.TRIANGLE_FAN&&K.mode!==void 0)return null;let H=$.extensions[this.name].attributes,Y=[],X={};for(let K in H)Y.push(this.parser.getDependency("accessor",H[K]).then((U)=>{return X[K]=U,X[K]}));if(Y.length<1)return null;return Y.push(this.parser.createNodeMesh(J)),Promise.all(Y).then((K)=>{let U=K.pop(),G=U.isGroup?U.children:[U],q=K[0].count,E=[];for(let F of G){let k=new vJ,M=new A,N=new A0,O=new A(1,1,1),C=new T7(F.geometry,F.material,q);for(let L=0;L<q;L++){if(X.TRANSLATION)M.fromBufferAttribute(X.TRANSLATION,L);if(X.ROTATION)N.fromBufferAttribute(X.ROTATION,L);if(X.SCALE)O.fromBufferAttribute(X.SCALE,L);C.setMatrixAt(L,k.compose(M,N,O))}for(let L in X)if(L==="_COLOR_0"){let w=X[L];C.instanceColor=new Z9(w.array,w.itemSize,w.normalized)}else if(L!=="TRANSLATION"&&L!=="ROTATION"&&L!=="SCALE")F.geometry.setAttribute(L,X[L]);Z0.prototype.copy.call(C,F),this.parser.assignFinalMaterial(C),E.push(C)}if(U.isGroup)return U.clear(),U.add(...E),U;return E[0]})}}var ZY="glTF",_6=12,fH={JSON:1313821514,BIN:5130562};class WY{constructor(J){this.name=gJ.KHR_BINARY_GLTF,this.content=null,this.body=null;let Q=new DataView(J,0,_6),$=new TextDecoder;if(this.header={magic:$.decode(new Uint8Array(J.slice(0,4))),version:Q.getUint32(4,!0),length:Q.getUint32(8,!0)},this.header.magic!==ZY)throw new Error("THREE.GLTFLoader: Unsupported glTF-Binary header.");else if(this.header.version<2)throw new Error("THREE.GLTFLoader: Legacy binary file detected.");let Z=this.header.length-_6,W=new DataView(J,_6),H=0;while(H<Z){let Y=W.getUint32(H,!0);H+=4;let X=W.getUint32(H,!0);if(H+=4,X===fH.JSON){let K=new Uint8Array(J,_6+H,Y);this.content=$.decode(K)}else if(X===fH.BIN){let K=_6+H;this.body=J.slice(K,K+Y)}H+=Y}if(this.content===null)throw new Error("THREE.GLTFLoader: JSON content not found.")}}class HY{constructor(J,Q){if(!Q)throw new Error("THREE.GLTFLoader: No DRACOLoader instance provided.");this.name=gJ.KHR_DRACO_MESH_COMPRESSION,this.json=J,this.dracoLoader=Q,this.dracoLoader.preload()}decodePrimitive(J,Q){let $=this.json,Z=this.dracoLoader,W=J.extensions[this.name].bufferView,H=J.extensions[this.name].attributes,Y={},X={},K={};for(let U in H){let G=r$[U]||U.toLowerCase();Y[G]=H[U]}for(let U in J.attributes){let G=r$[U]||U.toLowerCase();if(H[U]!==void 0){let q=$.accessors[J.attributes[U]],E=o9[q.componentType];K[G]=E.name,X[G]=q.normalized===!0}}return Q.getDependency("bufferView",W).then(function(U){return new Promise(function(G,q){Z.decodeDracoFile(U,function(E){for(let F in E.attributes){let k=E.attributes[F],M=X[F];if(M!==void 0)k.normalized=M}G(E)},Y,K,P0,q)})})}}class YY{constructor(){this.name=gJ.KHR_TEXTURE_TRANSFORM}extendTexture(J,Q){if((Q.texCoord===void 0||Q.texCoord===J.channel)&&Q.offset===void 0&&Q.rotation===void 0&&Q.scale===void 0)return J;if(J=J.clone(),Q.texCoord!==void 0)J.channel=Q.texCoord;if(Q.offset!==void 0)J.offset.fromArray(Q.offset);if(Q.rotation!==void 0)J.rotation=Q.rotation;if(Q.scale!==void 0)J.repeat.fromArray(Q.scale);return J.needsUpdate=!0,J}}class XY{constructor(){this.name=gJ.KHR_MESH_QUANTIZATION}}class JZ extends u8{constructor(J,Q,$,Z){super(J,Q,$,Z)}copySampleValue_(J){let Q=this.resultBuffer,$=this.sampleValues,Z=this.valueSize,W=J*Z*3+Z;for(let H=0;H!==Z;H++)Q[H]=$[W+H];return Q}interpolate_(J,Q,$,Z){let W=this.resultBuffer,H=this.sampleValues,Y=this.valueSize,X=Y*2,K=Y*3,U=Z-Q,G=($-Q)/U,q=G*G,E=q*G,F=J*K,k=F-K,M=-2*E+3*q,N=E-q,O=1-M,C=N-q+G;for(let L=0;L!==Y;L++){let w=H[k+L+Y],v=H[k+L+X]*U,_=H[F+L+Y],T=H[F+L]*U;W[L]=O*w+C*v+M*_+N*T}return W}}var Wq=new A0;class KY extends JZ{interpolate_(J,Q,$,Z){let W=super.interpolate_(J,Q,$,Z);return Wq.fromArray(W).normalize().toArray(W),W}}var i0={FLOAT:5126,FLOAT_MAT3:35675,FLOAT_MAT4:35676,FLOAT_VEC2:35664,FLOAT_VEC3:35665,FLOAT_VEC4:35666,LINEAR:9729,REPEAT:10497,SAMPLER_2D:35678,POINTS:0,LINES:1,LINE_LOOP:2,LINE_STRIP:3,TRIANGLES:4,TRIANGLE_STRIP:5,TRIANGLE_FAN:6,UNSIGNED_BYTE:5121,UNSIGNED_SHORT:5123},o9={5120:Int8Array,5121:Uint8Array,5122:Int16Array,5123:Uint16Array,5125:Uint32Array,5126:Float32Array},hH={9728:B8,9729:Z8,9984:E7,9985:v9,9986:H9,9987:C8},bH={33071:G7,33648:q7,10497:y9},o$={SCALAR:1,VEC2:2,VEC3:3,VEC4:4,MAT2:4,MAT3:9,MAT4:16},r$={POSITION:"position",NORMAL:"normal",TANGENT:"tangent",TEXCOORD_0:"uv",TEXCOORD_1:"uv1",TEXCOORD_2:"uv2",TEXCOORD_3:"uv3",COLOR_0:"color",WEIGHTS_0:"skinWeight",JOINTS_0:"skinIndex"},o8={scale:"scale",translation:"position",rotation:"quaternion",weights:"morphTargetInfluences"},Hq={CUBICSPLINE:void 0,LINEAR:D7,STEP:X$},i$={OPAQUE:"OPAQUE",MASK:"MASK",BLEND:"BLEND"};function Yq(J){if(J.DefaultMaterial===void 0)J.DefaultMaterial=new l9({color:16777215,emissive:0,metalness:1,roughness:1,transparent:!1,depthTest:!0,side:x8});return J.DefaultMaterial}function N9(J,Q,$){for(let Z in $.extensions)if(J[Z]===void 0)Q.userData.gltfExtensions=Q.userData.gltfExtensions||{},Q.userData.gltfExtensions[Z]=$.extensions[Z]}function T8(J,Q){if(Q.extras!==void 0)if(typeof Q.extras==="object")Object.assign(J.userData,Q.extras);else console.warn("THREE.GLTFLoader: Ignoring primitive type .extras, "+Q.extras)}function Xq(J,Q,$){let Z=!1,W=!1,H=!1;for(let U=0,G=Q.length;U<G;U++){let q=Q[U];if(q.POSITION!==void 0)Z=!0;if(q.NORMAL!==void 0)W=!0;if(q.COLOR_0!==void 0)H=!0;if(Z&&W&&H)break}if(!Z&&!W&&!H)return Promise.resolve(J);let Y=[],X=[],K=[];for(let U=0,G=Q.length;U<G;U++){let q=Q[U];if(Z){let E=q.POSITION!==void 0?$.getDependency("accessor",q.POSITION):J.attributes.position;Y.push(E)}if(W){let E=q.NORMAL!==void 0?$.getDependency("accessor",q.NORMAL):J.attributes.normal;X.push(E)}if(H){let E=q.COLOR_0!==void 0?$.getDependency("accessor",q.COLOR_0):J.attributes.color;K.push(E)}}return Promise.all([Promise.all(Y),Promise.all(X),Promise.all(K)]).then(function(U){let G=U[0],q=U[1],E=U[2];if(Z)J.morphAttributes.position=G;if(W)J.morphAttributes.normal=q;if(H)J.morphAttributes.color=E;return J.morphTargetsRelative=!0,J})}function Kq(J,Q){if(J.updateMorphTargets(),Q.weights!==void 0)for(let $=0,Z=Q.weights.length;$<Z;$++)J.morphTargetInfluences[$]=Q.weights[$];if(Q.extras&&Array.isArray(Q.extras.targetNames)){let $=Q.extras.targetNames;if(J.morphTargetInfluences.length===$.length){J.morphTargetDictionary={};for(let Z=0,W=$.length;Z<W;Z++)J.morphTargetDictionary[$[Z]]=Z}else console.warn("THREE.GLTFLoader: Invalid extras.targetNames length. Ignoring names.")}}function Uq(J){let Q,$=J.extensions&&J.extensions[gJ.KHR_DRACO_MESH_COMPRESSION];if($)Q="draco:"+$.bufferView+":"+$.indices+":"+a$($.attributes);else Q=J.indices+":"+a$(J.attributes)+":"+J.mode;if(J.targets!==void 0)for(let Z=0,W=J.targets.length;Z<W;Z++)Q+=":"+a$(J.targets[Z]);return Q}function a$(J){let Q="",$=Object.keys(J).sort();for(let Z=0,W=$.length;Z<W;Z++)Q+=$[Z]+":"+J[$[Z]]+";";return Q}function t$(J){switch(J){case Int8Array:return 0.007874015748031496;case Uint8Array:return 0.00392156862745098;case Int16Array:return 0.00003051850947599719;case Uint16Array:return 0.000015259021896696422;default:throw new Error("THREE.GLTFLoader: Unsupported normalized accessor component type.")}}function Gq(J){if(J.search(/\.jpe?g($|\?)/i)>0||J.search(/^data\:image\/jpeg/)===0)return"image/jpeg";if(J.search(/\.webp($|\?)/i)>0||J.search(/^data\:image\/webp/)===0)return"image/webp";if(J.search(/\.ktx2($|\?)/i)>0||J.search(/^data\:image\/ktx2/)===0)return"image/ktx2";return"image/png"}var qq=new vJ;class UY{constructor(J={},Q={}){this.json=J,this.extensions={},this.plugins={},this.options=Q,this.cache=new Zq,this.associations=new Map,this.primitiveCache={},this.nodeCache={},this.meshCache={refs:{},uses:{}},this.cameraCache={refs:{},uses:{}},this.lightCache={refs:{},uses:{}},this.sourceCache={},this.textureCache={},this.nodeNamesUsed={};let $=!1,Z=-1,W=!1,H=-1;if(typeof navigator!=="undefined"){let Y=navigator.userAgent;$=/^((?!chrome|android).)*safari/i.test(Y)===!0;let X=Y.match(/Version\/(\d+)/);Z=$&&X?parseInt(X[1],10):-1,W=Y.indexOf("Firefox")>-1,H=W?Y.match(/Firefox\/([0-9]+)\./)[1]:-1}if(typeof createImageBitmap==="undefined"||$&&Z<17||W&&H<98)this.textureLoader=new h7(this.options.manager);else this.textureLoader=new l7(this.options.manager);if(this.textureLoader.setCrossOrigin(this.options.crossOrigin),this.textureLoader.setRequestHeader(this.options.requestHeader),this.fileLoader=new z6(this.options.manager),this.fileLoader.setResponseType("arraybuffer"),this.options.crossOrigin==="use-credentials")this.fileLoader.setWithCredentials(!0)}setExtensions(J){this.extensions=J}setPlugins(J){this.plugins=J}parse(J,Q){let $=this,Z=this.json,W=this.extensions;this.cache.removeAll(),this.nodeCache={},this._invokeAll(function(H){return H._markDefs&&H._markDefs()}),Promise.all(this._invokeAll(function(H){return H.beforeRoot&&H.beforeRoot()})).then(function(){return Promise.all([$.getDependencies("scene"),$.getDependencies("animation"),$.getDependencies("camera")])}).then(function(H){let Y={scene:H[0][Z.scene||0],scenes:H[0],animations:H[1],cameras:H[2],asset:Z.asset,parser:$,userData:{}};return N9(W,Y,Z),T8(Y,Z),Promise.all($._invokeAll(function(X){return X.afterRoot&&X.afterRoot(Y)})).then(function(){for(let X of Y.scenes)X.updateMatrixWorld();J(Y)})}).catch(Q)}_markDefs(){let J=this.json.nodes||[],Q=this.json.skins||[],$=this.json.meshes||[];for(let Z=0,W=Q.length;Z<W;Z++){let H=Q[Z].joints;for(let Y=0,X=H.length;Y<X;Y++)J[H[Y]].isBone=!0}for(let Z=0,W=J.length;Z<W;Z++){let H=J[Z];if(H.mesh!==void 0){if(this._addNodeRef(this.meshCache,H.mesh),H.skin!==void 0)$[H.mesh].isSkinnedMesh=!0}if(H.camera!==void 0)this._addNodeRef(this.cameraCache,H.camera)}}_addNodeRef(J,Q){if(Q===void 0)return;if(J.refs[Q]===void 0)J.refs[Q]=J.uses[Q]=0;J.refs[Q]++}_getNodeRef(J,Q,$){if(J.refs[Q]<=1)return $;let Z=$.clone(),W=(H,Y)=>{let X=this.associations.get(H);if(X!=null)this.associations.set(Y,X);for(let[K,U]of H.children.entries())W(U,Y.children[K])};return W($,Z),Z.name+="_instance_"+J.uses[Q]++,Z}_invokeOne(J){let Q=Object.values(this.plugins);Q.push(this);for(let $=0;$<Q.length;$++){let Z=J(Q[$]);if(Z)return Z}return null}_invokeAll(J){let Q=Object.values(this.plugins);Q.unshift(this);let $=[];for(let Z=0;Z<Q.length;Z++){let W=J(Q[Z]);if(W)$.push(W)}return $}getDependency(J,Q){let $=J+":"+Q,Z=this.cache.get($);if(!Z){switch(J){case"scene":Z=this.loadScene(Q);break;case"node":Z=this._invokeOne(function(W){return W.loadNode&&W.loadNode(Q)});break;case"mesh":Z=this._invokeOne(function(W){return W.loadMesh&&W.loadMesh(Q)});break;case"accessor":Z=this.loadAccessor(Q);break;case"bufferView":Z=this._invokeOne(function(W){return W.loadBufferView&&W.loadBufferView(Q)});break;case"buffer":Z=this.loadBuffer(Q);break;case"material":Z=this._invokeOne(function(W){return W.loadMaterial&&W.loadMaterial(Q)});break;case"texture":Z=this._invokeOne(function(W){return W.loadTexture&&W.loadTexture(Q)});break;case"skin":Z=this.loadSkin(Q);break;case"animation":Z=this._invokeOne(function(W){return W.loadAnimation&&W.loadAnimation(Q)});break;case"camera":Z=this.loadCamera(Q);break;default:if(Z=this._invokeOne(function(W){return W!=this&&W.getDependency&&W.getDependency(J,Q)}),!Z)throw new Error("Unknown type: "+J);break}this.cache.add($,Z)}return Z}getDependencies(J){let Q=this.cache.get(J);if(!Q){let $=this,Z=this.json[J+(J==="mesh"?"es":"s")]||[];Q=Promise.all(Z.map(function(W,H){return $.getDependency(J,H)})),this.cache.add(J,Q)}return Q}loadBuffer(J){let Q=this.json.buffers[J],$=this.fileLoader;if(Q.type&&Q.type!=="arraybuffer")throw new Error("THREE.GLTFLoader: "+Q.type+" buffer type is not supported.");if(Q.uri===void 0&&J===0)return Promise.resolve(this.extensions[gJ.KHR_BINARY_GLTF].body);let Z=this.options;return new Promise(function(W,H){$.load(s8.resolveURL(Q.uri,Z.path),W,void 0,function(){H(new Error('THREE.GLTFLoader: Failed to load buffer "'+Q.uri+'".'))})})}loadBufferView(J){let Q=this.json.bufferViews[J];return this.getDependency("buffer",Q.buffer).then(function($){let Z=Q.byteLength||0,W=Q.byteOffset||0;return $.slice(W,W+Z)})}loadAccessor(J){let Q=this,$=this.json,Z=this.json.accessors[J];if(Z.bufferView===void 0&&Z.sparse===void 0){let H=o$[Z.type],Y=o9[Z.componentType],X=Z.normalized===!0,K=new Y(Z.count*H);return Promise.resolve(new F0(K,H,X))}let W=[];if(Z.bufferView!==void 0)W.push(this.getDependency("bufferView",Z.bufferView));else W.push(null);if(Z.sparse!==void 0)W.push(this.getDependency("bufferView",Z.sparse.indices.bufferView)),W.push(this.getDependency("bufferView",Z.sparse.values.bufferView));return Promise.all(W).then(function(H){let Y=H[0],X=o$[Z.type],K=o9[Z.componentType],U=K.BYTES_PER_ELEMENT,G=U*X,q=Z.byteOffset||0,E=Z.bufferView!==void 0?$.bufferViews[Z.bufferView].byteStride:void 0,F=Z.normalized===!0,k,M;if(E&&E!==G){let N=Math.floor(q/E),O="InterleavedBuffer:"+Z.bufferView+":"+Z.componentType+":"+N+":"+Z.count,C=Q.cache.get(O);if(!C)k=new K(Y,N*E,Z.count*E/U),C=new F6(k,E/U),Q.cache.add(O,C);M=new g9(C,X,q%E/U,F)}else{if(Y===null)k=new K(Z.count*X);else k=new K(Y,q,Z.count*X);M=new F0(k,X,F)}if(Z.sparse!==void 0){let N=o$.SCALAR,O=o9[Z.sparse.indices.componentType],C=Z.sparse.indices.byteOffset||0,L=Z.sparse.values.byteOffset||0,w=new O(H[1],C,Z.sparse.count*N),v=new K(H[2],L,Z.sparse.count*X);if(Y!==null)M=new F0(M.array.slice(),M.itemSize,M.normalized);M.normalized=!1;for(let _=0,T=w.length;_<T;_++){let x=w[_];if(M.setX(x,v[_*X]),X>=2)M.setY(x,v[_*X+1]);if(X>=3)M.setZ(x,v[_*X+2]);if(X>=4)M.setW(x,v[_*X+3]);if(X>=5)throw new Error("THREE.GLTFLoader: Unsupported itemSize in sparse BufferAttribute.")}M.normalized=F}return M})}loadTexture(J){let Q=this.json,$=this.options,W=Q.textures[J].source,H=Q.images[W],Y=this.textureLoader;if(H.uri){let X=$.manager.getHandler(H.uri);if(X!==null)Y=X}return this.loadTextureImage(J,W,Y)}loadTextureImage(J,Q,$){let Z=this,W=this.json,H=W.textures[J],Y=W.images[Q],X=(Y.uri||Y.bufferView)+":"+H.sampler;if(this.textureCache[X])return this.textureCache[X];let K=this.loadImageSource(Q,$).then(function(U){if(U.flipY=!1,U.name=H.name||Y.name||"",U.name===""&&typeof Y.uri==="string"&&Y.uri.startsWith("data:image/")===!1)U.name=Y.uri;let q=(W.samplers||{})[H.sampler]||{};return U.magFilter=hH[q.magFilter]||Z8,U.minFilter=hH[q.minFilter]||C8,U.wrapS=bH[q.wrapS]||y9,U.wrapT=bH[q.wrapT]||y9,U.generateMipmaps=!U.isCompressedTexture&&U.minFilter!==B8&&U.minFilter!==Z8,Z.associations.set(U,{textures:J}),U}).catch(function(){return null});return this.textureCache[X]=K,K}loadImageSource(J,Q){let $=this,Z=this.json,W=this.options;if(this.sourceCache[J]!==void 0)return this.sourceCache[J].then((G)=>G.clone());let H=Z.images[J],Y=self.URL||self.webkitURL,X=H.uri||"",K=!1;if(H.bufferView!==void 0)X=$.getDependency("bufferView",H.bufferView).then(function(G){K=!0;let q=new Blob([G],{type:H.mimeType});return X=Y.createObjectURL(q),X});else if(H.uri===void 0)throw new Error("THREE.GLTFLoader: Image "+J+" is missing URI and bufferView");let U=Promise.resolve(X).then(function(G){return new Promise(function(q,E){let F=q;if(Q.isImageBitmapLoader===!0)F=function(k){let M=new E0(k);M.needsUpdate=!0,q(M)};Q.load(s8.resolveURL(G,W.path),F,void 0,E)})}).then(function(G){if(K===!0)Y.revokeObjectURL(X);return T8(G,H),G.userData.mimeType=H.mimeType||Gq(H.uri),G}).catch(function(G){throw console.error("THREE.GLTFLoader: Couldn't load texture",X),G});return this.sourceCache[J]=U,U}assignTexture(J,Q,$,Z){let W=this;return this.getDependency("texture",$.index).then(function(H){if(!H)return null;if($.texCoord!==void 0&&$.texCoord>0)H=H.clone(),H.channel=$.texCoord;if(W.extensions[gJ.KHR_TEXTURE_TRANSFORM]){let Y=$.extensions!==void 0?$.extensions[gJ.KHR_TEXTURE_TRANSFORM]:void 0;if(Y){let X=W.associations.get(H);H=W.extensions[gJ.KHR_TEXTURE_TRANSFORM].extendTexture(H,Y),W.associations.set(H,X)}}if(Z!==void 0)H.colorSpace=Z;return J[Q]=H,H})}assignFinalMaterial(J){let{geometry:Q,material:$}=J,Z=Q.attributes.tangent===void 0,W=Q.attributes.color!==void 0,H=Q.attributes.normal===void 0;if(J.isPoints){let Y="PointsMaterial:"+$.uuid,X=this.cache.get(Y);if(!X)X=new L6,g0.prototype.copy.call(X,$),X.color.copy($.color),X.map=$.map,X.sizeAttenuation=!1,this.cache.add(Y,X);$=X}else if(J.isLine){let Y="LineBasicMaterial:"+$.uuid,X=this.cache.get(Y);if(!X)X=new D6,g0.prototype.copy.call(X,$),X.color.copy($.color),X.map=$.map,this.cache.add(Y,X);$=X}if(Z||W||H){let Y="ClonedMaterial:"+$.uuid+":";if(Z)Y+="derivative-tangents:";if(W)Y+="vertex-colors:";if(H)Y+="flat-shading:";let X=this.cache.get(Y);if(!X){if(X=$.clone(),W)X.vertexColors=!0;if(H)X.flatShading=!0;if(Z){if(X.normalScale)X.normalScale.y*=-1;if(X.clearcoatNormalScale)X.clearcoatNormalScale.y*=-1}this.cache.add(Y,X),this.associations.set(X,this.associations.get($))}$=X}J.material=$}getMaterialType(){return l9}loadMaterial(J){let Q=this,$=this.json,Z=this.extensions,W=$.materials[J],H,Y={},X=W.extensions||{},K=[];if(X[gJ.KHR_MATERIALS_UNLIT]){let G=Z[gJ.KHR_MATERIALS_UNLIT];H=G.getMaterialType(),K.push(G.extendParams(Y,W,Q))}else{let G=W.pbrMetallicRoughness||{};if(Y.color=new jJ(1,1,1),Y.opacity=1,Array.isArray(G.baseColorFactor)){let q=G.baseColorFactor;Y.color.setRGB(q[0],q[1],q[2],P0),Y.opacity=q[3]}if(G.baseColorTexture!==void 0)K.push(Q.assignTexture(Y,"map",G.baseColorTexture,d8));if(Y.metalness=G.metallicFactor!==void 0?G.metallicFactor:1,Y.roughness=G.roughnessFactor!==void 0?G.roughnessFactor:1,G.metallicRoughnessTexture!==void 0)K.push(Q.assignTexture(Y,"metalnessMap",G.metallicRoughnessTexture)),K.push(Q.assignTexture(Y,"roughnessMap",G.metallicRoughnessTexture));H=this._invokeOne(function(q){return q.getMaterialType&&q.getMaterialType(J)}),K.push(Promise.all(this._invokeAll(function(q){return q.extendMaterialParams&&q.extendMaterialParams(J,Y)})))}if(W.doubleSided===!0)Y.side=o0;let U=W.alphaMode||i$.OPAQUE;if(U===i$.BLEND)Y.transparent=!0,Y.depthWrite=!1;else if(Y.transparent=!1,U===i$.MASK)Y.alphaTest=W.alphaCutoff!==void 0?W.alphaCutoff:0.5;if(W.normalTexture!==void 0&&H!==G8){if(K.push(Q.assignTexture(Y,"normalMap",W.normalTexture)),Y.normalScale=new PJ(1,1),W.normalTexture.scale!==void 0){let G=W.normalTexture.scale;Y.normalScale.set(G,G)}}if(W.occlusionTexture!==void 0&&H!==G8){if(K.push(Q.assignTexture(Y,"aoMap",W.occlusionTexture)),W.occlusionTexture.strength!==void 0)Y.aoMapIntensity=W.occlusionTexture.strength}if(W.emissiveFactor!==void 0&&H!==G8){let G=W.emissiveFactor;Y.emissive=new jJ().setRGB(G[0],G[1],G[2],P0)}if(W.emissiveTexture!==void 0&&H!==G8)K.push(Q.assignTexture(Y,"emissiveMap",W.emissiveTexture,d8));return Promise.all(K).then(function(){let G=new H(Y);if(W.name)G.name=W.name;if(T8(G,W),Q.associations.set(G,{materials:J}),W.extensions)N9(Z,G,W);return G})}createUniqueName(J){let Q=oJ.sanitizeNodeName(J||"");if(Q in this.nodeNamesUsed)return Q+"_"+ ++this.nodeNamesUsed[Q];else return this.nodeNamesUsed[Q]=0,Q}loadGeometries(J){let Q=this,$=this.extensions,Z=this.primitiveCache;function W(Y){return $[gJ.KHR_DRACO_MESH_COMPRESSION].decodePrimitive(Y,Q).then(function(X){return xH(X,Y,Q)})}let H=[];for(let Y=0,X=J.length;Y<X;Y++){let K=J[Y],U=Uq(K),G=Z[U];if(G)H.push(G.promise);else{let q;if(K.extensions&&K.extensions[gJ.KHR_DRACO_MESH_COMPRESSION])q=W(K);else q=xH(new p0,K,Q);Z[U]={primitive:K,promise:q},H.push(q)}}return Promise.all(H)}loadMesh(J){let Q=this,$=this.json,Z=this.extensions,W=$.meshes[J],H=W.primitives,Y=[];for(let X=0,K=H.length;X<K;X++){let U=H[X].material===void 0?Yq(this.cache):this.getDependency("material",H[X].material);Y.push(U)}return Y.push(Q.loadGeometries(H)),Promise.all(Y).then(function(X){let K=X.slice(0,X.length-1),U=X[X.length-1],G=[];for(let E=0,F=U.length;E<F;E++){let k=U[E],M=H[E],N,O=K[E];if(M.mode===i0.TRIANGLES||M.mode===i0.TRIANGLE_STRIP||M.mode===i0.TRIANGLE_FAN||M.mode===void 0){if(N=W.isSkinnedMesh===!0?new I7(k,O):new C0(k,O),N.isSkinnedMesh===!0)N.normalizeSkinWeights();if(M.mode===i0.TRIANGLE_STRIP)N.geometry=s$(N.geometry,E6);else if(M.mode===i0.TRIANGLE_FAN)N.geometry=s$(N.geometry,b9)}else if(M.mode===i0.LINES)N=new A7(k,O);else if(M.mode===i0.LINE_STRIP)N=new p9(k,O);else if(M.mode===i0.LINE_LOOP)N=new S7(k,O);else if(M.mode===i0.POINTS)N=new j7(k,O);else throw new Error("THREE.GLTFLoader: Primitive mode unsupported: "+M.mode);if(Object.keys(N.geometry.morphAttributes).length>0)Kq(N,W);if(N.name=Q.createUniqueName(W.name||"mesh_"+J),T8(N,W),M.extensions)N9(Z,N,M);Q.assignFinalMaterial(N),G.push(N)}for(let E=0,F=G.length;E<F;E++)Q.associations.set(G[E],{meshes:J,primitives:E});if(G.length===1){if(W.extensions)N9(Z,G[0],W);return G[0]}let q=new Y8;if(W.extensions)N9(Z,q,W);Q.associations.set(q,{meshes:J});for(let E=0,F=G.length;E<F;E++)q.add(G[E]);return q})}loadCamera(J){let Q,$=this.json.cameras[J],Z=$[$.type];if(!Z){console.warn("THREE.GLTFLoader: Missing camera parameters.");return}if($.type==="perspective")Q=new O0(X9.radToDeg(Z.yfov),Z.aspectRatio||1,Z.znear||1,Z.zfar||2000000);else if($.type==="orthographic")Q=new m9(-Z.xmag,Z.xmag,Z.ymag,-Z.ymag,Z.znear,Z.zfar);if($.name)Q.name=this.createUniqueName($.name);return T8(Q,$),Promise.resolve(Q)}loadSkin(J){let Q=this.json.skins[J],$=[];for(let Z=0,W=Q.joints.length;Z<W;Z++)$.push(this._loadNodeShallow(Q.joints[Z]));if(Q.inverseBindMatrices!==void 0)$.push(this.getDependency("accessor",Q.inverseBindMatrices));else $.push(null);return Promise.all($).then(function(Z){let W=Z.pop(),H=Z,Y=[],X=[];for(let K=0,U=H.length;K<U;K++){let G=H[K];if(G){Y.push(G);let q=new vJ;if(W!==null)q.fromArray(W.array,K*16);X.push(q)}else console.warn('THREE.GLTFLoader: Joint "%s" could not be found.',Q.joints[K])}return new k6(Y,X)})}loadAnimation(J){let Q=this.json,$=this,Z=Q.animations[J],W=Z.name?Z.name:"animation_"+J,H=[],Y=[],X=[],K=[],U=[];for(let G=0,q=Z.channels.length;G<q;G++){let E=Z.channels[G],F=Z.samplers[E.sampler],k=E.target,M=k.node,N=Z.parameters!==void 0?Z.parameters[F.input]:F.input,O=Z.parameters!==void 0?Z.parameters[F.output]:F.output;if(k.node===void 0)continue;H.push(this.getDependency("node",M)),Y.push(this.getDependency("accessor",N)),X.push(this.getDependency("accessor",O)),K.push(F),U.push(k)}return Promise.all([Promise.all(H),Promise.all(Y),Promise.all(X),Promise.all(K),Promise.all(U)]).then(function(G){let q=G[0],E=G[1],F=G[2],k=G[3],M=G[4],N=[];for(let O=0,C=q.length;O<C;O++){let L=q[O],w=E[O],v=F[O],_=k[O],T=M[O];if(L===void 0)continue;if(L.updateMatrix)L.updateMatrix();let x=$._createAnimationTracks(L,w,v,_,T);if(x)for(let z=0;z<x.length;z++)N.push(x[z])}return new f7(W,void 0,N)})}createNodeMesh(J){let Q=this.json,$=this,Z=Q.nodes[J];if(Z.mesh===void 0)return null;return $.getDependency("mesh",Z.mesh).then(function(W){let H=$._getNodeRef($.meshCache,Z.mesh,W);if(Z.weights!==void 0)H.traverse(function(Y){if(!Y.isMesh)return;for(let X=0,K=Z.weights.length;X<K;X++)Y.morphTargetInfluences[X]=Z.weights[X]});return H})}loadNode(J){let Q=this.json,$=this,Z=Q.nodes[J],W=$._loadNodeShallow(J),H=[],Y=Z.children||[];for(let K=0,U=Y.length;K<U;K++)H.push($.getDependency("node",Y[K]));let X=Z.skin===void 0?Promise.resolve(null):$.getDependency("skin",Z.skin);return Promise.all([W,Promise.all(H),X]).then(function(K){let U=K[0],G=K[1],q=K[2];if(q!==null)U.traverse(function(E){if(!E.isSkinnedMesh)return;E.bind(q,qq)});for(let E=0,F=G.length;E<F;E++)U.add(G[E]);return U})}_loadNodeShallow(J){let Q=this.json,$=this.extensions,Z=this;if(this.nodeCache[J]!==void 0)return this.nodeCache[J];let W=Q.nodes[J],H=W.name?Z.createUniqueName(W.name):"",Y=[],X=Z._invokeOne(function(K){return K.createNodeMesh&&K.createNodeMesh(J)});if(X)Y.push(X);if(W.camera!==void 0)Y.push(Z.getDependency("camera",W.camera).then(function(K){return Z._getNodeRef(Z.cameraCache,W.camera,K)}));return Z._invokeAll(function(K){return K.createNodeAttachment&&K.createNodeAttachment(J)}).forEach(function(K){Y.push(K)}),this.nodeCache[J]=Promise.all(Y).then(function(K){let U;if(W.isBone===!0)U=new R6;else if(K.length>1)U=new Y8;else if(K.length===1)U=K[0];else U=new Z0;if(U!==K[0])for(let G=0,q=K.length;G<q;G++)U.add(K[G]);if(W.name)U.userData.name=W.name,U.name=H;if(T8(U,W),W.extensions)N9($,U,W);if(W.matrix!==void 0){let G=new vJ;G.fromArray(W.matrix),U.applyMatrix4(G)}else{if(W.translation!==void 0)U.position.fromArray(W.translation);if(W.rotation!==void 0)U.quaternion.fromArray(W.rotation);if(W.scale!==void 0)U.scale.fromArray(W.scale)}if(!Z.associations.has(U))Z.associations.set(U,{});else if(W.mesh!==void 0&&Z.meshCache.refs[W.mesh]>1){let G=Z.associations.get(U);Z.associations.set(U,{...G})}return Z.associations.get(U).nodes=J,U}),this.nodeCache[J]}loadScene(J){let Q=this.extensions,$=this.json.scenes[J],Z=this,W=new Y8;if($.name)W.name=Z.createUniqueName($.name);if(T8(W,$),$.extensions)N9(Q,W,$);let H=$.nodes||[],Y=[];for(let X=0,K=H.length;X<K;X++)Y.push(Z.getDependency("node",H[X]));return Promise.all(Y).then(function(X){for(let U=0,G=X.length;U<G;U++)W.add(X[U]);let K=(U)=>{let G=new Map;for(let[q,E]of Z.associations)if(q instanceof g0||q instanceof E0)G.set(q,E);return U.traverse((q)=>{let E=Z.associations.get(q);if(E!=null)G.set(q,E)}),G};return Z.associations=K(W),W})}_createAnimationTracks(J,Q,$,Z,W){let H=[],Y=J.name?J.name:J.uuid,X=[];if(o8[W.path]===o8.weights)J.traverse(function(q){if(q.morphTargetInfluences)X.push(q.name?q.name:q.uuid)});else X.push(Y);let K;switch(o8[W.path]){case o8.weights:K=L8;break;case o8.rotation:K=I8;break;case o8.translation:case o8.scale:K=V8;break;default:switch($.itemSize){case 1:K=L8;break;case 2:case 3:default:K=V8;break}break}let U=Z.interpolation!==void 0?Hq[Z.interpolation]:D7,G=this._getArrayFromAccessor($);for(let q=0,E=X.length;q<E;q++){let F=new K(X[q]+"."+o8[W.path],Q.array,G,U);if(Z.interpolation==="CUBICSPLINE")this._createCubicSplineTrackInterpolant(F);H.push(F)}return H}_getArrayFromAccessor(J){let Q=J.array;if(J.normalized){let $=t$(Q.constructor),Z=new Float32Array(Q.length);for(let W=0,H=Q.length;W<H;W++)Z[W]=Q[W]*$;Q=Z}return Q}_createCubicSplineTrackInterpolant(J){J.createInterpolant=function Q($){return new(this instanceof I8?KY:JZ)(this.times,this.values,this.getValueSize()/3,$)},J.createInterpolant.isInterpolantFactoryMethodGLTFCubicSpline=!0}}function Eq(J,Q,$){let Z=Q.attributes,W=new S0;if(Z.POSITION!==void 0){let X=$.json.accessors[Z.POSITION],K=X.min,U=X.max;if(K!==void 0&&U!==void 0){if(W.set(new A(K[0],K[1],K[2]),new A(U[0],U[1],U[2])),X.normalized){let G=t$(o9[X.componentType]);W.min.multiplyScalar(G),W.max.multiplyScalar(G)}}else{console.warn("THREE.GLTFLoader: Missing min/max properties for accessor POSITION.");return}}else return;let H=Q.targets;if(H!==void 0){let X=new A,K=new A;for(let U=0,G=H.length;U<G;U++){let q=H[U];if(q.POSITION!==void 0){let E=$.json.accessors[q.POSITION],F=E.min,k=E.max;if(F!==void 0&&k!==void 0){if(K.setX(Math.max(Math.abs(F[0]),Math.abs(k[0]))),K.setY(Math.max(Math.abs(F[1]),Math.abs(k[1]))),K.setZ(Math.max(Math.abs(F[2]),Math.abs(k[2]))),E.normalized){let M=t$(o9[E.componentType]);K.multiplyScalar(M)}X.max(K)}else console.warn("THREE.GLTFLoader: Missing min/max properties for accessor POSITION.")}}W.expandByVector(X)}J.boundingBox=W;let Y=new x0;W.getCenter(Y.center),Y.radius=W.min.distanceTo(W.max)/2,J.boundingSphere=Y}function xH(J,Q,$){let Z=Q.attributes,W=[];function H(Y,X){return $.getDependency("accessor",Y).then(function(K){J.setAttribute(X,K)})}for(let Y in Z){let X=r$[Y]||Y.toLowerCase();if(X in J.attributes)continue;W.push(H(Z[Y],X))}if(Q.indices!==void 0&&!J.index){let Y=$.getDependency("accessor",Q.indices).then(function(X){J.setIndex(X)});W.push(Y)}if(lJ.workingColorSpace!==P0&&"COLOR_0"in Z)console.warn(`THREE.GLTFLoader: Converting vertex colors from "srgb-linear" to "${lJ.workingColorSpace}" not supported.`);return T8(J,Q),Eq(J,Q,$),Promise.all(W).then(function(){return Q.targets!==void 0?Xq(J,Q.targets,$):J})}function Nq(J){if(J.dataset.ready)return;J.dataset.ready="true";let Q=J.querySelector("canvas"),$=J.querySelector('[role="status"]'),Z;try{Z=new m$({canvas:Q,antialias:!0,alpha:!0})}catch{J.dataset.failed="true",$.textContent="3D preview unavailable. Download the GLB model below.";return}Z.setPixelRatio(Math.min(devicePixelRatio,2)),Z.setClearColor(15855849,1);let W=new _7,H=new O0(35,1,0.1,5000);H.up.set(0,0,1);let Y=new n$(H,Q);Y.enableDamping=!0,Y.listenToKeyEvents(Q);let X=new b7(16777215,7829367,2.3);X.position.set(0,0,1),W.add(X);for(let[O,C]of[[[100,-150,250],3],[[-150,100,80],1.5]]){let L=new u9(16777215,C);L.position.set(...O),W.add(L)}let K=new e$,U,G,q=0;function E(){if(!U)return;let O=new S0().setFromObject(U),C=O.getCenter(new A);G=O.getSize(new A).length(),Y.target.copy(C);let L=X9.degToRad(H.fov),w=2*Math.atan(Math.tan(L/2)*H.aspect),v=G/2/Math.sin(Math.min(L,w)/2)*1.1;H.position.copy(C).add(new A(0.65,-0.95,0.9).normalize().multiplyScalar(v)),H.near=G/1000,H.far=G*15,H.updateProjectionMatrix(),Y.update()}async function F(O){let C=++q;$.textContent="Loading 3D assembly…";try{let L=await K.loadAsync(J.dataset[O]);if(C!==q)return;if(U)W.remove(U),U.traverse((w)=>{if(w.geometry?.dispose(),w.material)(Array.isArray(w.material)?w.material:[w.material]).forEach((v)=>v.dispose())});U=L.scene,W.add(U),E(),$.textContent=O==="exploded"?"Exploded assembly loaded. Drag to rotate; scroll to zoom.":"Assembled case loaded. Drag to rotate; scroll to zoom.",J.dataset.loaded=O,J.querySelectorAll("[data-mode]").forEach((w)=>w.setAttribute("aria-pressed",String(w.dataset.mode===O)))}catch{J.dataset.failed="true",$.textContent="Could not load the 3D preview. Download the GLB model below."}}J.querySelectorAll("[data-mode]").forEach((O)=>O.addEventListener("click",()=>F(O.dataset.mode))),J.querySelector("[data-reset]").addEventListener("click",E);let k=new ResizeObserver(()=>{let{clientWidth:O,clientHeight:C}=Q;Z.setSize(O,C,!1),H.aspect=O/C,H.updateProjectionMatrix()});k.observe(Q);let M;function N(){M=requestAnimationFrame(N),Y.update(),Z.render(W,H)}N(),F("assembled"),J.cleanup=()=>{++q,cancelAnimationFrame(M),k.disconnect(),Y.dispose(),U?.traverse((O)=>{if(O.geometry?.dispose(),O.material)(Array.isArray(O.material)?O.material:[O.material]).forEach((C)=>C.dispose())}),Z.dispose()}}function Oq(){document.querySelectorAll("[data-enclosure-viewer]").forEach(Nq)}Oq();
