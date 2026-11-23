import Icon, { type IconName } from './Icon'
import styles from './Medallion.module.css'

type Props = {
  icon: IconName
  tone?: 'light' | 'dark'
}

function Medallion({ icon, tone = 'light' }: Props) {
  return (
    <span className={`${styles.medallion} ${styles[tone]}`}>
      <Icon name={icon} />
    </span>
  )
}

export default Medallion
