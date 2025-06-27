const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');
const grid=16, size=canvas.width;
let snake=[{x:160, y:160}], dx=grid, dy=0;
let food={x:320, y:320};

function randPos(){ return Math.floor(Math.random()*(size/grid))*grid; }
function placeFood(){ food={x:randPos(), y:randPos()}; }
function update(){
  snake.unshift({x:snake[0].x+dx, y:snake[0].y+dy});
  if(snake[0].x===food.x && snake[0].y===food.y){ placeFood(); }
  else snake.pop();
  ctx.fillStyle='black'; ctx.fillRect(0,0,size,size);
  ctx.fillStyle='red'; ctx.fillRect(food.x,food.y,grid-1,grid-1);
  ctx.fillStyle='lime';
  snake.forEach((c,i)=>ctx.fillRect(c.x,c.y,grid-1,grid-1));
  if(snake[0].x<0||snake[0].x>=size||snake[0].y<0||snake[0].y>=size
      ||snake.slice(1).some(c=>c.x===snake[0].x&&c.y===snake[0].y)){
    snake=[{x:160,y:160}]; dx=grid; dy=0; placeFood();
  }
}
document.addEventListener('keydown',e=>{
  if(e.code==='ArrowUp'&&dy===0){dx=0;dy=-grid;}
  if(e.code==='ArrowDown'&&dy===0){dx=0;dy=grid;}
  if(e.code==='ArrowLeft'&&dx===0){dx=-grid;dy=0;}
  if(e.code==='ArrowRight'&&dx===0){dx=grid;dy=0;}
});
placeFood();
setInterval(update,1000/15);
