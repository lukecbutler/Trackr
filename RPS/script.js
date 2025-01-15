const rockButton = document.getElementById('rock')
const paperButton = document.getElementById('paper')
const scissorsButton = document.getElementById('scissors')

let userChoice
let computerChoice
let winner
let choices = ['rock', 'paper', 'scissors']


rockButton.addEventListener("click", getChoice)
paperButton.addEventListener("click", getChoice)
scissorsButton.addEventListener('click', getChoice)

function getChoice(event){
    if (event.target.id === 'rock'){
        document.getElementById('userImg').src="imgs/rock.png"
        userChoice = 'rock';

    }

    else if (event.target.id === 'paper'){
        document.getElementById('userImg').src='imgs/paper.png'
        userChoice = 'paper'
    }

    else if (event.target.id === 'scissors'){
        document.getElementById('userImg').src='imgs/scissors.png'
        userChoice = 'scissors'
    }



    computerChoice = getRandomElement(choices)

    if (computerChoice === 'rock'){
        document.getElementById('computerImg').src="imgs/rock.png"
    }

    else if (computerChoice === 'paper'){
        document.getElementById('computerImg').src='imgs/paper.png'
    }

    else if (computerChoice === 'scissors'){
        document.getElementById('computerImg').src='imgs/scissors.png'
    }

    document.getElementById('userChoice').innerHTML = userChoice
    document.getElementById('computerChoice').innerHTML = computerChoice

    winner = getWinner(userChoice, computerChoice)
    document.getElementById('winner').innerHTML = winner

}

function getWinner(userChoice, computerChoice){
    if (userChoice === 'rock' && computerChoice === 'rock'){
        winner = "Tie"
    }

    else if (userChoice === 'paper' && computerChoice === 'paper'){
        winner = "Tie"
    }
    
    else if (userChoice === 'scissors' && computerChoice === 'scissors'){
        winner = "Tie"
    }





    else if (userChoice === 'rock' && computerChoice === 'scissors'){
        winner = "User"
    }

    else if (userChoice === 'paper' && computerChoice === 'rock'){
        winner = "User"
    }
    
    else if (userChoice === 'scissors' && computerChoice === 'paper'){
        winner = "User"
    }






    else if (userChoice === 'rock' && computerChoice === 'paper'){
        winner = "Computer"
    }

    else if (userChoice === 'paper' && computerChoice === 'scissors'){
        winner = "Computer"
    }
    
    else if (userChoice === 'scissors' && computerChoice === 'rock'){
        winner = "Computer"
    }


    return winner;

}

function getRandomElement(choices) {
    const index = Math.floor(Math.random() * choices.length);
    return choices[index];
}